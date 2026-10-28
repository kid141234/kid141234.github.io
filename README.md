# 我的个人主页

中文为主的学生综合个人主页。纯 HTML、CSS、JavaScript，没有第三方依赖，也不需要编译。

## 打开页面

直接用浏览器打开 `dist/index.html` 即可查看。更推荐本地预览：

```powershell
cd 'E:\gy\个人主页\personal-homepage'
node preview.mjs
```

浏览器访问 `http://127.0.0.1:4173`。按 Ctrl+C 结束预览。若端口被占用，设置 `$env:PORT = '4174'` 后再启动。

## 我应该改哪个文件？

**日常更新只需编辑 `dist/content.js`，保存后刷新网页。**

- `profile`：姓名、英文名、学校、专业、所在地、照片、邮箱、简历、社交链接。
- `intro`：首屏问候、个人签名、简介。
- `about`：较详细的自我介绍，每一段为一个字符串。
- `focus`：关注方向，每一个方向为一个字符串。
- `education`：教育经历。
- `projects`：项目与作品。
- `publications`：论文。为空数组时，栏目和导航自动隐藏。
- `experience`：实习、工作、社团或志愿实践。为空时自动隐藏。
- `awards`：奖项。为空时自动隐藏。
- `interests`：兴趣、生活记录。
- `contact`：联系区域的标题和说明。

`""` 表示空文字，`[]` 表示暂时没有条目。保留引号和逗号；文字中需要英文双引号时使用 `\"`，或者改用中文引号。条目按照填写顺序展示，建议将最近经历放在前面。

教育、作品、兴趣未填写时会展示明确的占位内容。没有邮箱、简历或社交账号时，不会生成无效按钮。页面没有虚构论文、实习、奖项或个人背景。

### 填写示例

以下均为字段说明，不是真实个人经历。复制相应结构，替换 `content.js` 里的对应空数组，并填写自己的资料。

```javascript
// profile.links 内可填写：
links: [
  { label: "GitHub", url: "https://github.com/你的用户名", icon: "github" },
  { label: "Google Scholar", url: "https://scholar.google.com/citations?user=你的ID", icon: "school" }
],

about: ["介绍你的学校、专业和目前在做的事。", "介绍你的兴趣、学习方向或希望认识的人。"],
focus: ["你关注的方向", "另一个方向"],

education: [
  {
    school: "你的学校",
    major: "你的专业",
    degree: "你的学位",
    period: "入学年份 — 毕业年份 / 至今",
    description: "课程、学习方向或其他希望补充的介绍。"
  }
],

projects: [
  {
    title: "你的项目名称",
    date: "项目时间",
    description: "项目解决了什么问题，以及你负责的部分。",
    image: "", // 可填写 "assets/project.jpg"
    imageAlt: "项目图片的文字描述",
    tags: ["技术或主题"],
    links: [
      { label: "源代码", url: "https://github.com/你的用户名/项目名" }
    ]
  }
],

publications: [
  {
    title: "论文标题",
    authors: "作者列表",
    venue: "会议或期刊名称",
    year: "发表年份",
    links: [{ label: "论文", url: "https://example.com/paper" }]
  }
],

experience: [
  {
    organization: "单位或组织名称",
    role: "岗位或身份",
    period: "开始时间 — 结束时间",
    description: "具体做了什么，以及你的贡献。"
  }
],

awards: [
  { title: "奖项名称", organization: "颁发单位", date: "获奖时间" }
],

interests: [
  {
    title: "兴趣或生活记录的标题",
    description: "一两句介绍。",
    icon: "camera", // camera、book、compass 等
    image: "", // 可填写 "assets/life.jpg"
    imageAlt: "图片的文字描述",
    url: "" // 可选：相册、文章等完整网址
  }
],
```

### 照片与简历

将文件放入 `dist/assets/`，然后填写 `profile.avatar: "assets/avatar.jpg"`、`profile.resume: "assets/resume.pdf"`。图片建议使用 JPG、PNG、WebP；文件名尽量简短、不要带空格。默认头像是原创小树苗插画，可以直接替换。头像加载失败会回退到插画；作品、兴趣图片加载失败会保留文字内容。

### 邮箱和外部链接

邮箱直接填写地址，例如 `name@example.com`。社交、论文、项目链接填写完整的 `https://...` 地址。本地图片和简历使用 `assets/...` 相对路径。邮箱填写后会显示邮件链接和复制按钮；复制权限不可用时会提示手动复制。

## 调整外观

- `dist/styles.css` 顶部的 `--blue` 是强调色，`--bg` 是背景色。
- `dist/app.js` 负责渲染内容、隐藏空栏目、导航高亮与复制邮箱。
- `dist/index.html` 是网页入口。
- `dist/assets/` 存放照片、简历、图标等资源。

页面适配桌面和手机，支持键盘导航及系统减少动画设置。所有字体来自设备本地，无需第三方字体或脚本服务。

## 发布到 GitHub Pages

你的 GitHub 用户名是 `kid141234`，个人主页仓库是 **`kid141234/kid141234.github.io`**，发布成功后网址为 **https://kid141234.github.io/**。

项目已准备好 `.github/workflows/pages.yml`：推送到 `main` 后，自动检查脚本并发布 `dist/`。不需要安装依赖，也不需要自定义域名。

1. 使用公开仓库 `kid141234/kid141234.github.io`。
2. 将本项目作为仓库根目录推送到 `main`，包括 `.github/workflows/pages.yml` 和 `dist/`。
3. 在仓库 **Settings → Pages → Build and deployment → Source** 选择 **GitHub Actions**。
4. 在 **Actions** 中检查部署结果；成功后访问 https://kid141234.github.io/ 。如果首次推送早于 Pages 设置，点击 **Run workflow** 再运行一次。

之后只需修改 `dist/content.js` 或添加 `dist/assets/` 内的文件，再提交到 `main`，网站会自动更新。浏览器直接编辑 GitHub 上的内容文件也可以触发更新。

也可采用不使用自定义工作流的方式：将 `dist/` **内部文件** 上传至仓库根目录（包含 `.nojekyll`），Pages 选择 **Deploy from a branch → main → /(root)**。此时不要同时上传上述工作流。两种发布方式选择一种即可。

GitHub 官方说明：https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site

## 语法检查

已安装 Node.js 时可运行 `npm run check`。此命令仅检查 JavaScript 语法，不会安装依赖。
