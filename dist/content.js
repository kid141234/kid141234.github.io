/* 你的主页内容都在这里修改。保存后刷新页面即可，无需编译。
 * 空字符串 "" 表示暂未填写；空数组 [] 表示暂无条目。
 * publications、experience、awards 为空时，整个栏目及导航自动隐藏。
 * 各类条目的填写示例见项目目录中的 README.md。
 */
window.HOMEPAGE = {
  profile: {
    name: "高源",
    englishName: "",
    role: "学生",
    school: "",
    major: "",
    location: "",
    avatar: "", // 将照片放入 assets 文件夹，填写 "assets/你的照片.jpg"
    email: "",
    resume: "", // 例如 "assets/resume.pdf"；留空不显示简历按钮
    links: [
      { label: "GitHub", url: "https://github.com/kid141234", icon: "github" }
    ] // 可继续添加 Google Scholar、博客等链接
  },
  intro: {
    greeting: "你好，我是",
    tagline: "保持好奇，慢慢积累。",
    description: "这里记录我的学习、作品与生活。欢迎来到我的个人主页。"
  },
  about: [], // 每一段介绍写成一个字符串，例如 ["第一段介绍。", "第二段介绍。"]
  focus: [], // 关注的方向，例如 ["方向一", "方向二"]
  education: [],
  projects: [],
  publications: [],
  experience: [],
  awards: [],
  interests: [],
  contact: {
    heading: "很高兴，在这里遇见你。",
    description: "关于学习、作品，或任何有趣的想法，都欢迎交流。"
  }
};
