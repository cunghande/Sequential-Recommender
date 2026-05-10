# Xóa thư mục frontend cũ
Remove-Item -Recurse -Force .\frontend

# Đổi tên thư mục frontnew thành frontend
Rename-Item -Path .\frontnew -NewName frontend

# Xóa file hướng dẫn cũ
Remove-Item -Force .\Huong_Dan_Chay_Du_An.md

# Khởi tạo git và tải lên GitHub
git init
git add .
git commit -m "Cleanup project, add Docker, .env, and update README"
git branch -M main
git remote add origin https://github.com/cunghande/Do_An_2_AI_Project.git
git push -u origin main --force
