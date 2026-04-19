import logging
import time
import mysql.connector
from mysql.connector import Error

# ==========================================
# 1. KONFIGURASI LOGGING TERMINAL
# ==========================================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ==========================================
# 2. KELAS UTAMA: AUTOSCALER
# ==========================================
class BelajarBarengAutoScaler:
    def __init__(self, db_config, group_id, max_capacity=5, min_capacity=1):
        self.db_config = db_config
        self.group_id = group_id
        self.current_capacity = min_capacity
        self.max_capacity = max_capacity
        self.min_capacity = min_capacity

    def log_to_database(self, active_users_count, action):
        """Menyimpan riwayat scaling ke dalam tabel scaling_logs"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            if conn.is_connected():
                cursor = conn.cursor()
                query = """
                    INSERT INTO scaling_logs (group_id, active_users_count, action)
                    VALUES (%s, %s, %s)
                """
                cursor.execute(query, (self.group_id, active_users_count, action))
                conn.commit()
                logging.info(f"[DB LOG] Aktivitas '{action}' berhasil dicatat ke tabel scaling_logs.")
        except Error as e:
            logging.error(f"[DB ERROR] Gagal mencatat ke database: {e}")
        finally:
            if 'conn' in locals() and conn.is_connected():
                cursor.close()
                conn.close()

    def get_active_users_from_db(self):
        """Menghitung jumlah user dinamis berdasarkan tabel group_members"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            query = "SELECT COUNT(*) FROM group_members WHERE group_id = %s"
            cursor.execute(query, (self.group_id,))
            result = cursor.fetchone()
            return result[0] if result else 0
        except Error as e:
            logging.error(f"[DB ERROR] Gagal mengambil data user: {e}")
            return 0
        finally:
            if 'conn' in locals() and conn.is_connected():
                cursor.close()
                conn.close()

    def evaluate_traffic(self):
        """Memantau jumlah pengguna langsung dari Database dan menentukan tindakan"""
        active_users = self.get_active_users_from_db()
        logging.info(f"[MONITORING] Group ID: {self.group_id} | Pengguna Aktif di DB: {active_users} | Kapasitas Server: {self.current_capacity}")
        
        if active_users > 50:
            self.scale_up(active_users)
        elif active_users < 10:
            self.scale_down(active_users)
        else:
            logging.info("[STABIL] Pengguna antara 10-50. Tidak ada tindakan scaling.\n")

    def scale_up(self, active_users):
        """Logika Scale-Up & Pencatatan ke DB"""
        if self.current_capacity < self.max_capacity:
            self.current_capacity += 1
            action_desc = f"SCALE_UP_TO_{self.current_capacity}"
            logging.warning(f"[SCALE-UP TRIGGERED] Menambah kapasitas menjadi {self.current_capacity}.")
            
            # (Simulasi) Di sini OaC Infrastruktur berjalan...
            time.sleep(1) 
            
            self.log_to_database(active_users_count=active_users, action=action_desc)
            logging.info("[SUCCESS] Kapasitas berhasil ditambahkan.\n")
        else:
            logging.error(f"[LIMIT REACHED] Kapasitas maksimum ({self.max_capacity}) tercapai!\n")

    def scale_down(self, active_users):
        """Logika Scale-Down & Pencatatan ke DB"""
        if self.current_capacity > self.min_capacity:
            self.current_capacity -= 1
            action_desc = f"SCALE_DOWN_TO_{self.current_capacity}"
            logging.warning(f"[SCALE-DOWN TRIGGERED] Mengurangi kapasitas menjadi {self.current_capacity}.")
            
            # (Simulasi) Di sini OaC Infrastruktur berjalan...
            time.sleep(1)
            
            self.log_to_database(active_users_count=active_users, action=action_desc)
            logging.info("[SUCCESS] Kapasitas berhasil dikurangi.\n")
        else:
            logging.info(f"[MINIMUM CAPACITY] Harus menyisakan minimal {self.min_capacity} kapasitas aktif.\n")

# ==========================================
# 3. BLOK SIMULASI UNTUK TESTING
# ==========================================
if __name__ == "__main__":
    print("=== Memulai Uji Coba Auto-Scaling BelajarBareng ===")
    
    # ---------------------------------------------------------
    # UBAH BAGIAN INI JIKA PASSWORD ROOT MYSQL ANDA BERBEDA
    # ---------------------------------------------------------
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': 'root', # Isi jika root MySQL Anda menggunakan password
        'database': 'db_belajar_bareng'
    }

    # Fungsi Helper: Mengatur jumlah data dummy di database agar bisa diuji
    def ubah_jumlah_member_simulasi(config, group_id, target_jumlah):
        print(f"\n[SYSTEM] Sedang menyuntikkan {target_jumlah} user dummy ke database untuk simulasi...")
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()

        # 1. Pastikan ada user pembuat & grup simulasi (Bypass foreign key check untuk mempermudah tes)
        cursor.execute("SET FOREIGN_KEY_CHECKS=0")
        cursor.execute("INSERT IGNORE INTO users (id, name, email, password) VALUES (999, 'Admin', 'admin@test.com', 'pass')")
        cursor.execute("INSERT IGNORE INTO study_groups (id, creator_id, name) VALUES (%s, 999, 'Grup Simulasi OaC')", (group_id,))
        
        # 2. Hapus member lama di grup ini agar jumlahnya sesuai target
        cursor.execute("DELETE FROM group_members WHERE group_id = %s", (group_id,))
        
        # 3. Masukkan jumlah user sesuai target simulasi
        for i in range(1, target_jumlah + 1):
            user_id = 1000 + i
            cursor.execute("INSERT IGNORE INTO users (id, name, email, password) VALUES (%s, %s, %s, 'pass')", (user_id, f"User {i}", f"user{i}@test.com"))
            cursor.execute("INSERT INTO group_members (group_id, user_id) VALUES (%s, %s)", (group_id, user_id))
        
        cursor.execute("SET FOREIGN_KEY_CHECKS=1")
        conn.commit()
        cursor.close()
        conn.close()

    # --- MULAI SKENARIO PENGUJIAN ---
    GROUP_TEST_ID = 1
    scaler = BelajarBarengAutoScaler(db_config=db_config, group_id=GROUP_TEST_ID)

    try:
        # Skenario 1: Kondisi Stabil (Misal 15 orang)
        ubah_jumlah_member_simulasi(db_config, GROUP_TEST_ID, target_jumlah=15)
        scaler.evaluate_traffic()
        time.sleep(2)

        # Skenario 2: Kondisi Ramai Tiba-tiba (Misal 60 orang -> Harus Scale UP)
        ubah_jumlah_member_simulasi(db_config, GROUP_TEST_ID, target_jumlah=60)
        scaler.evaluate_traffic()
        time.sleep(2)

        # Skenario 3: Kondisi Sepi (Misal 5 orang -> Harus Scale DOWN)
        ubah_jumlah_member_simulasi(db_config, GROUP_TEST_ID, target_jumlah=5)
        scaler.evaluate_traffic()

        print("\n=== PENGUJIAN SELESAI ===")
        print("Silakan cek tabel 'scaling_logs' di database Anda (misal via phpMyAdmin/DBeaver).")
        print("Anda seharusnya melihat record log Scale Up dan Scale Down di sana.")

    except Error as e:
        print(f"\n[GAGAL SIMULASI] Terjadi error saat menghubungi MySQL: {e}")
        print("Pastikan server MySQL menyala dan kredensial (username/password) di 'db_config' sudah benar.")