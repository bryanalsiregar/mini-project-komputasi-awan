import subprocess
import time
import concurrent.futures

# Konfigurasi
TOTAL_RUNS = 100
SCRIPT_TARGET = "provision_wadah_belajar.py"

def run_provisioning(run_id):
    """Fungsi untuk menjalankan command terminal 1 kali"""
    name = f"Grup Load Test {run_id}"
    desc = f"Ini adalah grup hasil testing otomatis ke-{run_id}"
    
    # Menyusun perintah terminal
    command = [
        "python", SCRIPT_TARGET,
        "--user_id", "101",
        "--name", name,
        "--desc", desc
    ]
    
    try:
        # Menjalankan perintah secara diam-diam (capture_output=True)
        result = subprocess.run(command, capture_output=True, text=True)
        
        if result.returncode == 0:
            return f"[OK] Run {run_id} berhasil."
        else:
            return f"[ERROR] Run {run_id} gagal. Log: {result.stderr.strip()}"
    except Exception as e:
        return f"[FATAL] Run {run_id} gagal dieksekusi: {e}"

def test_create_sequential():
    """Testing Fitur Create: Dijalankan berurutan satu per satu"""
    print(f"--- MEMULAI SEQUENTIAL TEST ({TOTAL_RUNS} KALI) ---")
    start_time = time.time()
    
    for i in range(1, TOTAL_RUNS + 1):
        status = run_provisioning(i)
        print(status)
        
    end_time = time.time()
    print(f"--- WAKTU TOTAL SEQUENTIAL: {end_time - start_time:.2f} detik ---\n")

def test_autoscaling_concurrent():
    """Testing Auto-Scaling / Load: Dijalankan BERSAMAAN (Paralel)"""
    print(f"--- MEMULAI CONCURRENT/AUTO-SCALING TEST ({TOTAL_RUNS} KALI) ---")
    start_time = time.time()
    
    # Menggunakan ThreadPool untuk menembak command secara bersamaan
    # max_workers = jumlah eksekusi simultan. Kita set 20 agar tidak membuat laptop hang.
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        # Submit semua 100 tugas sekaligus
        futures = [executor.submit(run_provisioning, i) for i in range(1, TOTAL_RUNS + 1)]
        
        # Ambil hasil seiring tugas selesai
        for future in concurrent.futures.as_completed(futures):
            print(future.result())
            
    end_time = time.time()
    print(f"--- WAKTU TOTAL CONCURRENT: {end_time - start_time:.2f} detik ---\n")

if __name__ == "__main__":
    print("PILIH MODE TESTING:")
    print("1. Sequential (Satu per satu - Normal Create Test)")
    print("2. Concurrent (Bersamaan - Auto-Scaling / Load Test)")
    
    pilihan = input("Masukkan pilihan (1/2): ")
    
    if pilihan == '1':
        test_create_sequential()
    elif pilihan == '2':
        test_autoscaling_concurrent()
    else:
        print("Pilihan tidak valid.")