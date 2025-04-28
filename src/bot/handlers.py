import os
import datetime
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import x25519
from utils.treekem import TreeNode
from utils.crypto import aes_encrypt
from utils.watermark import dct_watermark_color, encode_lsb

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class PhotoEncryptBot:
    def __init__(self, app):
        self.app = app
        self.share_requests = {}  # {user_id: {"chat_id": group_id}}
        self.pending_photos = (
            {}
        )  # {group_id: {"sender_id": user_id, "original_path": str, "photo_path": str, "requested_users": list, "timestamp": str}}
        self.setup_handlers()

        os.makedirs("output/original", exist_ok=True)
        os.makedirs("output/encrypted", exist_ok=True)
        os.makedirs("output/decrypted", exist_ok=True)
        os.makedirs("output/extracted", exist_ok=True)
        os.makedirs("output/keys", exist_ok=True)

    def get_user_key_path(self, user_id):
        """Get path to user's private key file"""
        return os.path.join(PROJECT_ROOT, "output", "keys", f"user_{user_id}_key.pem")

    def load_or_generate_key(self, user_id):
        """Load existing key or generate new one if not exists"""
        key_path = self.get_user_key_path(user_id)

        if os.path.exists(key_path):
            with open(key_path, "rb") as f:
                private_key = x25519.X25519PrivateKey.from_private_bytes(f.read())
            print(f"Loaded existing key for user {user_id}")
        else:
            private_key = x25519.X25519PrivateKey.generate()
            with open(key_path, "wb") as f:
                f.write(
                    private_key.private_bytes(
                        encoding=serialization.Encoding.Raw,
                        format=serialization.PrivateFormat.Raw,
                        encryption_algorithm=serialization.NoEncryption(),
                    )
                )
            print(f"Generated new key for user {user_id}")

        return private_key

    def setup_handlers(self):
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("share", self.share))
        self.app.add_handler(
            MessageHandler(
                filters.PHOTO & filters.ChatType.PRIVATE, self.handle_private_photo
            )
        )
        self.app.add_handler(
            MessageHandler(
                filters.TEXT & filters.ChatType.GROUPS, self.handle_group_text
            )
        )

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "👋 欢迎使用照片加密分享机器人！\n\n"
            "使用 /share 在群组中分享照片\n"
            "发送照片给机器人添加数字水印"
        )

    async def share(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id

        self.share_requests[user_id] = {"chat_id": chat_id}

        await context.bot.send_message(chat_id=user_id, text="请发送您要分享的照片")

        await update.message.reply_text("我已向您发送私聊消息，请在那里发送照片")

    async def handle_private_photo(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        user_id = update.effective_user.id

        if user_id not in self.share_requests:
            return

        chat_id = self.share_requests[user_id]["chat_id"]
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        readable_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Download and save original photo
        photo_file = await update.message.photo[-1].get_file()
        original_path = f"output/original/photo_{user_id}_{timestamp}.png"
        temp_path = f"temp_share_{user_id}.png"
        await photo_file.download_to_drive(original_path)
        await photo_file.download_to_drive(temp_path)

        # Store in pending photos with timestamp
        self.pending_photos[chat_id] = {
            "sender_id": user_id,
            "original_path": original_path,
            "photo_path": temp_path,
            "requested_users": [user_id],
            "timestamp": timestamp,
            "readable_timestamp": readable_timestamp,
        }

        await context.bot.send_message(
            chat_id=chat_id,
            text=f"用户 {user_id} 分享了一张照片\n\n如需查看，请回复: /view_{user_id}",
        )

        await update.message.reply_text("照片已接收，已在群组发布分享通知")

        try:
            os.remove(temp_path)
            print(f"已删除临时文件: {temp_path}")
        except Exception as e:
            print(f"删除临时文件失败: {e}")

    async def handle_group_text(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        text = update.message.text

        if not text.startswith("/view_") or chat_id not in self.pending_photos:
            return

        try:
            target_user_id = int(text[6:])
            if self.pending_photos[chat_id]["sender_id"] != target_user_id:
                return

            # Add requesting user
            if user_id not in self.pending_photos[chat_id]["requested_users"]:
                self.pending_photos[chat_id]["requested_users"].append(user_id)

            # Generate key tree
            root = TreeNode()

            # 1. Sender's key
            sender_private = self.load_or_generate_key(target_user_id)
            sender_public = sender_private.public_key()
            root.add_member_TreeNode(sender_public)

            # 2. Requesters' keys
            for uid in self.pending_photos[chat_id]["requested_users"]:
                if uid != target_user_id:
                    private_key = self.load_or_generate_key(uid)
                    public_key = private_key.public_key()
                    root.add_member_TreeNode(public_key)

            root.update_key_TreeNode()
            derived_key = root.group_key

            # 使用原始图片的时间戳
            timestamp = self.pending_photos[chat_id]["timestamp"]
            readable_timestamp = self.pending_photos[chat_id]["readable_timestamp"]

            # Save derived key with receiver ID and original timestamp
            derived_key_filename = f"derived_key_{user_id}_{timestamp}.bin"
            with open(
                os.path.join(PROJECT_ROOT, "output", "encrypted", derived_key_filename),
                "wb",
            ) as file:
                file.write(derived_key)

            # Prepare watermark info
            member_info = "\n".join(
                [str(uid) for uid in self.pending_photos[chat_id]["requested_users"]]
            )

            # Process photo with receiver ID and original timestamp
            output_path = await self._process_photo(
                chat_id,
                self.pending_photos[chat_id]["original_path"],
                readable_timestamp,
                member_info,
                derived_key,
                user_id,
                timestamp,
            )

            # Send to user
            await context.bot.send_photo(
                chat_id=user_id,
                photo=open(output_path, "rb"),
                caption=f"🖼️ 来自用户 {target_user_id} 的分享照片\n"
                f"时间戳: {readable_timestamp}\n"
                f"接收者ID: {user_id}",
            )

        except Exception as e:
            print(f"处理查看请求时出错: {e}")

    async def _process_photo(
        self,
        chat_id,
        input_path,
        timestamp,
        member_info,
        derived_key,
        receiver_id,
        file_timestamp,
    ):
        # Prepare LSB watermark
        lsb_text = f"""=== 安全水印 ===
群组ID: {chat_id}
时间戳: {timestamp}
成员列表:
{member_info}
=== 结束 ===
"""
        encrypted_lsb = aes_encrypt(lsb_text.encode(), derived_key)
        lsb_length = len(encrypted_lsb)

        # Append LSB length to derived key file
        derived_key_filename = f"derived_key_{receiver_id}_{file_timestamp}.bin"
        with open(
            os.path.join(PROJECT_ROOT, "output", "encrypted", derived_key_filename),
            "ab",
        ) as file:
            file.write(lsb_length.to_bytes(4, byteorder="big"))

        # Generate output filenames with receiver ID and original timestamp
        dct_output = os.path.join(
            PROJECT_ROOT, f"output/decrypted/dct_{receiver_id}_{file_timestamp}.png"
        )
        lsb_output = os.path.join(
            PROJECT_ROOT, f"output/decrypted/lsb_{receiver_id}_{file_timestamp}.png"
        )
        final_output = os.path.join(
            PROJECT_ROOT, f"output/decrypted/final_{receiver_id}_{file_timestamp}.png"
        )

        # Apply watermarks
        dct_watermark_color(
            input_path,
            os.path.join(PROJECT_ROOT, "data/watermarks/watermark.png"),
            dct_output,
            alpha=0.05,
        )

        encode_lsb(dct_output, encrypted_lsb, lsb_output)
        os.rename(lsb_output, final_output)

        return final_output