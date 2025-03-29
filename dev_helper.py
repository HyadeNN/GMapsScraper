import os
import shutil

# Hedef klasörün adı
TARGET_DIR = "files_to_send"

# Listeyi kaydedeceğimiz dosyanın adı
LIST_FILE = "list_of_projectfiles_paths.txt"

# Bulunduğunuz dizin
BASE_DIR = os.getcwd()

# Kopyalanmayacak dosyalar
EXCLUDED_FILES = {
    "dev_helper.py",
    "DOCUMENTATION.md",
    "README.md",
    "LICENSE",
    "Pipfile.lock",
    "files_to_send",
    ".gitignore",
    ".git",
    ".vscode",
    ".idea",
    "package-lock.json",
    "list_of_projectfiles_paths.txt",
    "yarn.lock",
    "setup_guide.txt",
    "__init__.py",
    "list.txt",
    "yedek.rar",
}

# Listelemede göz ardı edilecek klasörler
EXCLUDED_DIRS = {
    "__pycache__",
    "__init__",
    "venv",
    ".venv",
    ".idea",
    ".env",
    "Pipfile",
    "node_modules",
    "content",
    "files_to_send",
    ".git",
    "build",
    "dist",
}

# Mod seçimi
print("Hangi modda çalıştırmak istersiniz?")
print("1 - Aynı dizin yapısını koruyarak kopyala")
print(
    "2 - Tüm dosyaları direkt olarak files_to_send içine kopyala (alt klasörler olmadan)"
)
mode = input("Seçiminiz (1/2): ").strip()

if mode not in {"1", "2"}:
    print("Geçersiz seçim! Program sonlandırılıyor.")
    exit(1)

# Hedef klasörü oluştur (yoksa)
os.makedirs(TARGET_DIR, exist_ok=True)

# Path listesini tutacak liste
file_paths = []

# Dosyaları listeleme ve kopyalama
for root, dirs, files in os.walk(BASE_DIR):
    # files_to_send ve node_modules klasörlerini atla
    if any(ex_dir in root.split(os.sep) for ex_dir in EXCLUDED_DIRS):
        continue

    # Dosyaları işleme
    for file in files:
        # İstenmeyen dosyaları atla
        if file in EXCLUDED_FILES:
            continue

        # Dosyanın relative pathini al ve listeye ekle
        relative_path = os.path.relpath(os.path.join(root, file), BASE_DIR)
        file_paths.append(relative_path)
        print(relative_path)

        # Mod 1: Aynı dizin yapısını koruyarak kopyala
        if mode == "1":
            target_path = os.path.join(TARGET_DIR, relative_path)
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
        # Mod 2: Tüm dosyaları direkt olarak files_to_send içine kopyala
        elif mode == "2":
            target_path = os.path.join(TARGET_DIR, file)

        # Eğer hedefte aynı isimde bir dosya varsa klasör adını ekle
        if os.path.exists(target_path):
            folder_name = os.path.basename(os.path.dirname(relative_path))
            name, ext = os.path.splitext(file)
            new_name = f"{name} - ({folder_name}){ext}"
            target_path = os.path.join(TARGET_DIR, new_name)

        # Dosyayı kopyala
        shutil.copy2(os.path.join(root, file), target_path)

# Path listesini dosyaya kaydet
with open(LIST_FILE, "w") as f:
    for path in file_paths:
        f.write(path + "\n")

print(f"\nDosyalar '{TARGET_DIR}' klasörüne kopyalandı.")
print(f"Dosya pathleri '{LIST_FILE}' dosyasına kaydedildi.")
