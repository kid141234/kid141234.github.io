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
- `blog`：独立文章卡片。目前留空，文章已全部归入「优化」专题；往里加卡片会让主页重新出现散落的文章卡片。
- `topics`：学习笔记里的专题（标题、简介、专题首页链接和文章 / 笔记列表）。John Lee 部分由 `build_notes.py` 生成，「优化」部分由 `build_blog.py` 插到数组最前面，详见下文。
- `publications`：论文。为空数组时，栏目和导航自动隐藏。
- `experience`：实习、工作、社团或志愿实践。为空时自动隐藏。
- `awards`：奖项。为空时自动隐藏。
- `interests`：兴趣、生活记录。
- `contact`：联系区域的标题和说明。

`""` 表示空文字，`[]` 表示暂时没有条目。保留引号和逗号；文字中需要英文双引号时使用 `\"`，或者改用中文引号。条目按照填写顺序展示，建议将最近经历放在前面。

### 专题：优化

「学习笔记」栏目现在是**两个并列的可点击专题入口卡片**：**优化**（3 篇文章，排在前面）与 **John Lee**（10 篇笔记，排在后面）。主页只显示专题卡片，不展开文章列表；点进专题首页才能看到全部条目。

**优化** 专题的入口是 `dist/blog/optimization/index.html`。专题名称、简介以及每篇文章的 `slug`、标题、简介、栏目标签、渲染开关和排列顺序，统一放在 `blog/optimization/meta.json`。安装 Python 包 `markdown-it-py` 后，在项目根目录运行 `python build_blog.py`，脚本会生成：

- `dist/blog/<slug>.html`：文章阅读页，公式由 MathJax 加载渲染，需要访问 jsDelivr。
- `dist/blog/optimization/index.html`：专题首页，列出全部 3 篇文章。
- `dist/content.js` 末尾带 `BEGIN 优化专题 / END 优化专题` 标记的数据段：把专题插入 `topics` 数组最前面。**这段由脚本生成，不要手工改动。**

新增一篇优化文章：把 Markdown 放进 `blog/`，在 `meta.json` 的 `articles` 中加一条（`slug` 与文件名一致），重新运行脚本即可。`articles` 的顺序决定专题首页的列表。配置里 `html: true` 的文章会保留源文件中的内联 `<figure>`/`<svg>` 示意图、参考文献锚点等（示意图的颜色变量定义在 `dist/blog/blog.css` 的 `.article` 规则中）。

`content.js` 的 `blog` 数组请保持为空。两个专题各由自己的脚本维护标记区块，互不覆盖，运行顺序不限。

### 学习笔记专题：John Lee

「学习笔记」栏目收录了专题 **John Lee**，是《Introduction to Smooth Manifolds》的 10 篇读书笔记。**该专题在主页只显示一个可点击的入口卡片，不展开笔记列表；点进专题首页 `dist/blog/john-lee/index.html` 才能看到全部 10 篇。** 专题数据来自 `dist/content.js` 中带 `BEGIN 专题 / END 专题` 标记的 `topics` 区块，**这个区块由脚本自动生成，不要手工改动**；其中 `notes` 目前只用于主页显示篇数、生成专题首页和每篇的上下篇导航。

相关文件：

- `blog/john-lee/*.tex`：从 `John Lee/*.zip` 解压出的 LaTeX 源文件（每个压缩包内是一个 `main.tex`）。
- `blog/john-lee/meta.json`：专题名称与简介，以及每篇笔记的 `slug`、标题、简介和排列顺序。
- `build_notes.py`：把 LaTeX 转成 HTML，并同步 `content.js` 中 John Lee 的 `topics` 区块（不会覆盖末尾的「优化」专题数据段）。

在项目根目录运行：

```powershell
python build_notes.py
```

脚本会生成或覆盖：

- `dist/blog/john-lee/*.html`：10 篇笔记阅读页，含目录、定理框、MathJax 公式和上一篇 / 下一篇导航。
- `dist/blog/john-lee/index.html`：专题首页。
- `dist/blog/notes.css`：定理框、列表和公式块样式。

**新增一篇笔记**：把新笔记的 `main.tex` 解压成 `blog/john-lee/<slug>.tex`，在 `meta.json` 的 `notes` 里按目标顺序加一条（`slug` 与文件名一致），重新运行脚本即可。`notes` 的顺序决定专题首页的列表和每篇的上一篇 / 下一篇，主页专题卡片上的篇数会自动更新（主页本身不会列出这些笔记）。

每篇 LaTeX 导言区里的 `\newcommand` 会自动转成该页的 MathJax 宏；公式仍需访问 jsDelivr 加载 MathJax 才能渲染。

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

### 用 API 脚本发布（github.com 的 git 端点不可达时）

若网络只放行 `api.github.com`、常规 `git push` 被代理拦截，可用 `publish_to_github.py`。它走 GitHub Git Data API，基于远端 `main` 的最新提交追加一次 commit，保留完整历史，不需要 force push，也不需要在本地建 git 仓库。

```powershell
python publish_to_github.py --dry-run     # 只读预览变更，无需 token
$env:GITHUB_TOKEN = "ghp_..."             # fine-grained token 需 Contents: read/write
python publish_to_github.py
```

脚本按 `.gitignore` 收集本地文件，逐文件比对远端 blob 的 SHA，只上传新增和修改的文件（也会处理删除），最后更新 `refs/heads/main`。token 只从环境变量读取，不会写入文件或打印。发布成功后 GitHub Actions 会自动部署 `dist/`。

## 语法检查

已安装 Node.js 时可运行 `npm run check`。此命令仅检查 JavaScript 语法，不会安装依赖。
