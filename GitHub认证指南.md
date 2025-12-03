# GitHub认证指南

## 🔑 重要提醒

GitHub已经不再支持直接使用密码进行Git操作。您需要创建Personal Access Token。

## 📝 创建Personal Access Token步骤

### 1. 登录GitHub
- 打开 [https://github.com](https://github.com)
- 使用您的邮箱：`776815438@qq.com` 和密码登录

### 2. 进入设置
- 点击右上角头像
- 选择"Settings"

### 3. 创建Token
- 在左侧菜单中选择"Developer settings"
- 选择"Personal access tokens"
- 选择"Tokens (classic)"
- 点击"Generate new token"

### 4. 配置Token
```
Note: 票据OCR识别工具项目
Expiration: 选择合适的过期时间（推荐90天）
Scopes: 勾选以下权限：
✅ repo (完整的仓库访问权限)
✅ workflow (GitHub Actions)
```

### 5. 生成并复制Token
- 点击"Generate token"
- **立即复制Token**（只显示一次！）
- 保存到安全的地方

## 🚀 推送步骤

### 方法1: 使用Token认证
创建完Token后，使用以下命令：

```bash
cd "D:\Work\202512\票据识别工具"
git remote add origin https://您的用户名@github.com/您的用户名/invoice-ocr-tool.git
git push -u origin master
```

当提示输入密码时，输入您的Personal Access Token。

### 方法2: 配置Git凭证
```bash
git config --global credential.helper store
git push -u origin master
# 然后输入用户名和Token
```

## ⚠️ 注意事项

1. **Token安全**：
   - Token等同于密码，请妥善保管
   - 不要在代码或公共地方分享
   - 定期更换Token

2. **用户名确认**：
   - 确认您的GitHub用户名（不是邮箱）
   - 在GitHub个人主页可以查看用户名

3. **仓库权限**：
   - 确保有仓库的推送权限
   - 如果是组织仓库，需要管理员权限

## 🔧 常见问题

### 问题1: "Authentication failed"
- 检查Token是否正确
- 确认Token没有过期
- 验证仓库URL中的用户名

### 问题2: "Repository not found"
- 确认仓库名称正确
- 检查仓库是否存在
- 验证是否有访问权限

### 问题3: "Permission denied"
- 检查Token权限设置
- 确认是仓库所有者或协作者
- 联系仓库管理员

## 📞 完成推送

成功推送后，您会看到：
```
Enumerating objects: 32, done.
Counting objects: 100% (32/32), done.
Delta compression using up to 8 threads
Compressing objects: 100% (25/25), done.
Writing objects: 100% (32/32), XXX KB | XXXX KB/s, done.
Total 32 (delta 8), reused 0 (delta 0), pack-reused 0
To https://github.com/用户名/invoice-ocr-tool.git
 * [new branch]      master -> master
Branch 'master' set up to track remote branch 'master' from 'origin'.
```

## 🎯 下一步

推送成功后，您可以：
- 在GitHub查看您的项目
- 分享项目链接
- 继续开发并推送更新
- 设置GitHub Pages展示项目

---

**需要帮助？** 如果遇到问题，请随时告诉我具体的错误信息！