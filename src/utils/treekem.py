from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
import os

class TreeNode:
    def __init__(self):
        self.children = []
        self.group_key = None
        self.private_key = self.generate_private_key()
        self.public_key = self.private_key.public_key()

    def generate_private_key(self):
        """Generate a new X25519 private key"""
        return x25519.X25519PrivateKey.generate()

    def compute_shared_key(self, peer_public_key):
        """Compute shared secret using X25519 key exchange"""
        return self.private_key.exchange(peer_public_key)

    def add_member_TreeNode(self, new_public_key):
        """Add a new member node with the given public key"""
        new_node = TreeNode()
        new_node.public_key = new_public_key
        self.children.append(new_node)
        self.update_key_TreeNode()

    def remove_member_TreeNode(self, public_key_to_remove):
        """Remove a member node with the specified public key"""
        for child in self.children:
            if child.public_key == public_key_to_remove:
                self.children.remove(child)
                self.update_key_TreeNode()
                break

    def update_key_TreeNode(self):
        """Update the group key for this node and its subtree"""
        self.group_key = self.generate_group_key_TreeNode()

    def generate_group_key_TreeNode(self):
        """
        Generate group key using X25519 shared secrets with all children:
        - For leaf nodes: return public key as identifier
        - For internal nodes: derive key from shared secrets with all children
        """
        if not self.children:
            # Leaf node returns its public key
            return self.public_key.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw
            )
        
        # Compute shared secrets with all children
        shared_keys = [
            self.compute_shared_key(child.public_key)
            for child in self.children
        ]
        
        # Combine all shared secrets
        combined_key = b''.join(shared_keys)
        
        # Derive final group key using HKDF
        return HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=os.urandom(16),
            info=b'treekem_group_key',
        ).derive(combined_key)

    def print_tree(self, level=0):
        """Print the tree structure with keys"""
        if not self.children:
            print("  " * level + 
                 f"Leaf Node Level {level}: Public Key: {self.public_key.public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw).hex()}")
        else:
            print("  " * level + 
                 f"Node Level {level}: Group Key: {self.group_key.hex() if self.group_key else 'None'}")
        for child in self.children:
            child.print_tree(level + 1)