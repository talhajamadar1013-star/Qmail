#!/usr/bin/env python3
"""
QuMail - Quantum Secure Email Client (Tkinter Version)
Alternative GUI using tkinter (built into Python)
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
from pathlib import Path
import threading
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

try:
    from config.settings import load_config
    from qumail_client.embedded_km.local_key_manager import get_embedded_key_manager
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you've installed the minimal requirements and run setup.py")
    sys.exit(1)

class QuMailTkinterApp:
    """QuMail GUI using tkinter"""
    
    def __init__(self):
        self.config = load_config()
        self.root = tk.Tk()
        self.km = None
        self.setup_gui()
        self.initialize_km()
    
    def setup_gui(self):
        """Setup the main GUI"""
        self.root.title(self.config.WINDOW_TITLE)
        self.root.geometry("1000x700")
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.create_compose_tab()
        self.create_inbox_tab()
        self.create_keys_tab()
        self.create_settings_tab()
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def create_compose_tab(self):
        """Create compose email tab"""
        compose_frame = ttk.Frame(self.notebook)
        self.notebook.add(compose_frame, text="✉️ Compose")
        
        # Email form
        ttk.Label(compose_frame, text="To:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.to_entry = ttk.Entry(compose_frame, width=50)
        self.to_entry.grid(row=0, column=1, columnspan=2, sticky="ew", padx=5, pady=5)
        
        ttk.Label(compose_frame, text="Subject:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.subject_entry = ttk.Entry(compose_frame, width=50)
        self.subject_entry.grid(row=1, column=1, columnspan=2, sticky="ew", padx=5, pady=5)
        
        ttk.Label(compose_frame, text="Message:").grid(row=2, column=0, sticky="nw", padx=5, pady=5)
        self.message_text = scrolledtext.ScrolledText(compose_frame, height=15, width=60)
        self.message_text.grid(row=2, column=1, columnspan=2, sticky="nsew", padx=5, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(compose_frame)
        button_frame.grid(row=3, column=1, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="📎 Attach File", command=self.attach_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🔐 Encrypt & Send", command=self.encrypt_and_send).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="💾 Save Draft", command=self.save_draft).pack(side=tk.LEFT, padx=5)
        
        # Attachments list
        ttk.Label(compose_frame, text="Attachments:").grid(row=4, column=0, sticky="nw", padx=5, pady=5)
        self.attachments_listbox = tk.Listbox(compose_frame, height=4)
        self.attachments_listbox.grid(row=4, column=1, columnspan=2, sticky="ew", padx=5, pady=5)
        
        # Configure grid weights
        compose_frame.columnconfigure(1, weight=1)
        compose_frame.rowconfigure(2, weight=1)
    
    def create_inbox_tab(self):
        """Create inbox tab"""
        inbox_frame = ttk.Frame(self.notebook)
        self.notebook.add(inbox_frame, text="📥 Inbox")
        
        # Email list
        columns = ("From", "Subject", "Date", "Status")
        self.email_tree = ttk.Treeview(inbox_frame, columns=columns, show="headings", height=10)
        
        for col in columns:
            self.email_tree.heading(col, text=col)
            self.email_tree.column(col, width=150)
        
        self.email_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Email content
        self.email_content = scrolledtext.ScrolledText(inbox_frame, height=15)
        self.email_content.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(inbox_frame)
        button_frame.pack(pady=5)
        
        ttk.Button(button_frame, text="🔄 Refresh", command=self.refresh_inbox).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🔓 Decrypt", command=self.decrypt_email).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="📥 Download Attachments", command=self.download_attachments).pack(side=tk.LEFT, padx=5)
    
    def create_keys_tab(self):
        """Create quantum keys management tab"""
        keys_frame = ttk.Frame(self.notebook)
        self.notebook.add(keys_frame, text="🔑 Quantum Keys")
        
        # Keys list
        columns = ("Key ID", "Status", "Created", "Length", "Protocol")
        self.keys_tree = ttk.Treeview(keys_frame, columns=columns, show="headings", height=12)
        
        for col in columns:
            self.keys_tree.heading(col, text=col)
            self.keys_tree.column(col, width=120)
        
        self.keys_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Key info
        info_frame = ttk.LabelFrame(keys_frame, text="Key Information")
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.key_info_text = scrolledtext.ScrolledText(info_frame, height=6)
        self.key_info_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(keys_frame)
        button_frame.pack(pady=5)
        
        ttk.Button(button_frame, text="🔑 Generate New Key", command=self.generate_key).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🔄 Refresh Keys", command=self.refresh_keys).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="📊 Statistics", command=self.show_km_stats).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🧹 Cleanup Expired", command=self.cleanup_expired_keys).pack(side=tk.LEFT, padx=5)
    
    def create_settings_tab(self):
        """Create settings tab"""
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="⚙️ Settings")
        
        # Configuration display
        config_frame = ttk.LabelFrame(settings_frame, text="Current Configuration")
        config_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.config_text = scrolledtext.ScrolledText(config_frame, height=20)
        self.config_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Load configuration
        self.load_config_display()
        
        # Buttons
        button_frame = ttk.Frame(settings_frame)
        button_frame.pack(pady=5)
        
        ttk.Button(button_frame, text="🔄 Reload Config", command=self.load_config_display).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🧪 Test Connections", command=self.test_connections).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="📝 Edit .env", command=self.edit_env_file).pack(side=tk.LEFT, padx=5)
    
    def initialize_km(self):
        """Initialize embedded key manager"""
        try:
            self.km = get_embedded_key_manager(self.config)
            self.status_var.set("✅ Embedded Key Manager initialized")
            self.refresh_keys()
        except Exception as e:
            self.status_var.set(f"❌ Key Manager error: {e}")
            messagebox.showerror("Key Manager Error", f"Failed to initialize Key Manager:\n{e}")
    
    def generate_key(self):
        """Generate a new quantum key"""
        def generate():
            try:
                self.status_var.set("🔑 Generating quantum key...")
                self.root.update()
                
                user_id = "test_user@qumail.local"  # In real app, get from login
                key_data = self.km.generate_quantum_key(user_id, self.config.DEFAULT_KEY_LENGTH)
                
                self.status_var.set(f"✅ Generated key: {key_data['key_id']}")
                self.refresh_keys()
                
                messagebox.showinfo("Key Generated", 
                    f"New quantum key generated!\n\n"
                    f"Key ID: {key_data['key_id']}\n"
                    f"Length: {key_data['key_length']} bytes\n"
                    f"Protocol: {key_data.get('quantum_protocol', 'BB84')}")
                
            except Exception as e:
                self.status_var.set(f"❌ Key generation failed: {e}")
                messagebox.showerror("Key Generation Error", f"Failed to generate key:\n{e}")
        
        threading.Thread(target=generate, daemon=True).start()
    
    def refresh_keys(self):
        """Refresh keys list"""
        if not self.km:
            return
        
        try:
            # Clear existing items
            for item in self.keys_tree.get_children():
                self.keys_tree.delete(item)
            
            # Get user keys
            user_id = "test_user@qumail.local"
            keys = self.km.get_user_keys(user_id, limit=100)
            
            for key in keys:
                created = datetime.fromisoformat(key['timestamp']).strftime("%Y-%m-%d %H:%M")
                self.keys_tree.insert("", "end", values=(
                    key['key_id'][:16] + "...",
                    key['status'],
                    created,
                    f"{key['key_length']} bytes",
                    key.get('quantum_protocol', 'BB84')
                ))
            
            self.status_var.set(f"📊 {len(keys)} keys loaded")
            
        except Exception as e:
            self.status_var.set(f"❌ Error loading keys: {e}")
    
    def show_km_stats(self):
        """Show key manager statistics"""
        if not self.km:
            return
        
        try:
            stats = self.km.get_statistics()
            
            info = f"""📊 Key Manager Statistics
            
Total Keys: {stats.get('total_keys', 0)}
Unused Keys: {stats.get('unused_keys', 0)}
Used Keys: {stats.get('used_keys', 0)}
Expired Keys: {stats.get('expired_keys', 0)}
Unique Users: {stats.get('unique_users', 0)}

Database: {stats.get('database_path', 'Unknown')}
Storage: {self.config.LOCAL_DATA_PATH}
"""
            
            self.key_info_text.delete(1.0, tk.END)
            self.key_info_text.insert(1.0, info)
            
        except Exception as e:
            messagebox.showerror("Statistics Error", f"Failed to get statistics:\n{e}")
    
    def cleanup_expired_keys(self):
        """Cleanup expired keys"""
        if not self.km:
            return
        
        try:
            count = self.km.cleanup_expired_keys()
            messagebox.showinfo("Cleanup Complete", f"Marked {count} expired keys for cleanup")
            self.refresh_keys()
        except Exception as e:
            messagebox.showerror("Cleanup Error", f"Failed to cleanup keys:\n{e}")
    
    def load_config_display(self):
        """Load and display configuration"""
        try:
            config_info = f"""🔧 QuMail Configuration

Environment: {self.config.ENVIRONMENT}
Debug Mode: {self.config.DEBUG}

🔑 Key Manager:
Embedded KM: {self.config.ENABLE_EMBEDDED_KM}
Local Storage: {self.config.LOCAL_DATA_PATH}
Key Encryption: {'Enabled' if self.config.KEY_ENCRYPTION_PASSWORD else 'Default'}

🗄️ Database:
Neon Host: {self.config.NEON_DB_HOST or 'Not configured'}
Database: {self.config.NEON_DB_NAME}
User: {self.config.NEON_DB_USER}

🌐 Blockchain:
Network: {self.config.POLYGON_NETWORK_NAME}
Chain ID: {self.config.POLYGON_CHAIN_ID}
RPC URL: {'Configured' if self.config.POLYGON_RPC_URL else 'Not configured'}

📁 IPFS:
Pinata API: {'Configured' if self.config.PINATA_API_KEY else 'Not configured'}
Storage: {'Enabled' if self.config.ENABLE_IPFS_STORAGE else 'Disabled'}

🔐 Encryption:
Algorithm: {self.config.ENCRYPTION_ALGORITHM}
Protocol: {self.config.QUANTUM_PROTOCOL}
Key Length: {self.config.DEFAULT_KEY_LENGTH} bytes

✨ Features:
Blockchain Verification: {self.config.ENABLE_BLOCKCHAIN_VERIFICATION}
IPFS Storage: {self.config.ENABLE_IPFS_STORAGE}
Email Encryption: {self.config.ENABLE_EMAIL_ENCRYPTION}
Offline Mode: {self.config.ENABLE_OFFLINE_MODE}
"""
            
            self.config_text.delete(1.0, tk.END)
            self.config_text.insert(1.0, config_info)
            
        except Exception as e:
            self.config_text.delete(1.0, tk.END)
            self.config_text.insert(1.0, f"❌ Error loading configuration: {e}")
    
    def test_connections(self):
        """Test external connections"""
        def test():
            self.status_var.set("🧪 Testing connections...")
            
            results = []
            
            # Test blockchain
            if self.config.ENABLE_BLOCKCHAIN_VERIFICATION and self.config.POLYGON_RPC_URL:
                try:
                    from web3 import Web3
                    web3 = Web3(Web3.HTTPProvider(self.config.get_polygon_rpc_url()))
                    if web3.is_connected():
                        block = web3.eth.block_number
                        results.append(f"✅ Blockchain: Connected (Block {block})")
                    else:
                        results.append("❌ Blockchain: Connection failed")
                except Exception as e:
                    results.append(f"❌ Blockchain: {e}")
            else:
                results.append("⏭️ Blockchain: Disabled or not configured")
            
            # Test IPFS
            if self.config.ENABLE_IPFS_STORAGE and self.config.PINATA_API_KEY:
                try:
                    import requests
                    headers = {
                        'pinata_api_key': self.config.PINATA_API_KEY,
                        'pinata_secret_api_key': self.config.PINATA_SECRET_KEY
                    }
                    response = requests.get(
                        f"{self.config.PINATA_BASE_URL}/data/testAuthentication",
                        headers=headers,
                        timeout=10
                    )
                    if response.status_code == 200:
                        results.append("✅ IPFS (Pinata): Connected")
                    else:
                        results.append(f"❌ IPFS: HTTP {response.status_code}")
                except Exception as e:
                    results.append(f"❌ IPFS: {e}")
            else:
                results.append("⏭️ IPFS: Disabled or not configured")
            
            # Test database
            if self.config.get_database_url():
                try:
                    # Test database connection would go here
                    results.append("⏭️ Database: Testing not implemented")
                except Exception as e:
                    results.append(f"❌ Database: {e}")
            else:
                results.append("⏭️ Database: Not configured")
            
            # Show results
            result_text = "\n".join(results)
            messagebox.showinfo("Connection Test Results", result_text)
            self.status_var.set("✅ Connection tests completed")
        
        threading.Thread(target=test, daemon=True).start()
    
    def edit_env_file(self):
        """Open .env file for editing"""
        env_path = project_root / '.env'
        messagebox.showinfo("Edit Configuration", 
            f"Please edit the .env file manually:\n\n{env_path}\n\n"
            f"After editing, restart QuMail or click 'Reload Config'.")
    
    def attach_file(self):
        """Attach file to email"""
        file_path = filedialog.askopenfilename(
            title="Select file to attach",
            filetypes=[("All files", "*.*")]
        )
        if file_path:
            self.attachments_listbox.insert(tk.END, file_path)
    
    def encrypt_and_send(self):
        """Encrypt and send email"""
        messagebox.showinfo("Not Implemented", 
            "Email encryption and sending will be implemented in the next phase.\n\n"
            "This demo focuses on the embedded Key Manager functionality.")
    
    def save_draft(self):
        """Save email draft"""
        messagebox.showinfo("Not Implemented", "Draft saving not yet implemented.")
    
    def refresh_inbox(self):
        """Refresh inbox"""
        messagebox.showinfo("Not Implemented", "Email receiving not yet implemented.")
    
    def decrypt_email(self):
        """Decrypt selected email"""
        messagebox.showinfo("Not Implemented", "Email decryption not yet implemented.")
    
    def download_attachments(self):
        """Download email attachments"""
        messagebox.showinfo("Not Implemented", "Attachment download not yet implemented.")
    
    def run(self):
        """Start the GUI application"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.root.quit()

def main():
    """Main application entry point"""
    print("🚀 Starting QuMail with tkinter GUI...")
    
    try:
        app = QuMailTkinterApp()
        app.run()
    except Exception as e:
        print(f"❌ Application error: {e}")
        messagebox.showerror("Application Error", f"QuMail failed to start:\n{e}")

if __name__ == "__main__":
    main()