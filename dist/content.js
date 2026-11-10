/* 你的主页内容都在这里修改。保存后刷新页面即可，无需编译。
 * 空字符串 "" 表示暂未填写；空数组 [] 表示暂无条目。
 * publications、experience、awards 为空时，整个栏目及导航自动隐藏。
 * 各类条目的填写示例见项目目录中的 README.md。
 */
window.HOMEPAGE = {
  profile: {
    name: "高源", // 姓名只需在这里修改；标题、名片和页脚会自动更新
    englishName: "",
    role: "学生",
    school: "北京邮电大学",
    major: "",
    location: "",
    avatar: "", // 将照片放入 assets 文件夹，填写 "assets/你的照片.jpg"
    email: "3509628398@qq.com",
    resume: "", // 例如 "assets/resume.pdf"；留空不显示简历按钮
    links: [
      { label: "GitHub", url: "https://github.com/kid141234", icon: "github" }
    ] // 可继续添加 Google Scholar、博客等链接
  },
  intro: {
    greeting: "你好，我是", // 这里只写问候语，不用重复填写姓名
    tagline: "保持好奇，慢慢积累。",
    description: "这里记录我的学习、作品与生活。欢迎来到我的个人主页。"
  },
  about: [], // 每一段介绍写成一个字符串，例如 ["第一段介绍。", "第二段介绍。"]
  focus: [], // 关注的方向，例如 ["方向一", "方向二"]
  education: [],
  projects: [],
  // 独立文章卡片：已全部归入「优化」专题（见 blog/optimization/meta.json 与文件末尾）
  blog: [],
  // --- BEGIN 专题：由 build_notes.py 生成，请勿手工改动 ---
  topics: [
    {
      "title": "John Lee",
      "english": "SMOOTH MANIFOLDS",
      "description": "《Introduction to Smooth Manifolds》读书笔记。从下沉与嵌入、Sard 定理，到向量场与流、向量丛、张量和微分形式，按教材章节顺序整理的 10 篇专题笔记。",
      "url": "blog/john-lee/index.html",
      "notes": [
        {
          "title": "下沉、浸入与嵌入总结",
          "description": "第 4 章：秩定理与常秩映射，下沉、浸入、嵌入、局部微分同胚，纤维与截面，覆叠映射及概念关系图。",
          "url": "blog/john-lee/submersions-immersions-embeddings.html"
        },
        {
          "title": "子流形",
          "description": "第 5 章：嵌入与浸入子流形、切片图、水平集与常秩定理、限制映射、拓扑唯一性，以及子流形的切空间刻画。",
          "url": "blog/john-lee/submanifolds.html"
        },
        {
          "title": "Sard 定理及其应用",
          "description": "第 6 章：零测度集与 Sard 定理，Whitney 嵌入与逼近定理，管状邻域，以及横截性与参数横截性定理。",
          "url": "blog/john-lee/sard-theorem.html"
        },
        {
          "title": "向量场、李群与李代数",
          "description": "推前与 F-related 向量场、李括号及其自然性，李群的左不变向量场、矩阵李代数、同态诱导与 Ado 定理。",
          "url": "blog/john-lee/vector-fields-lie-groups.html"
        },
        {
          "title": "积分曲线与流",
          "description": "第 9 章：积分曲线与流的基本定理、自然性、完备向量场判别、流出定理、奇点规范形、李导数与时间依赖流。",
          "url": "blog/john-lee/integral-curves-flows.html"
        },
        {
          "title": "向量丛与纤维丛",
          "description": "第 10 章：向量丛的定义与例子、局部平凡化与过渡函数、截面与标架、丛同态、子丛，以及纤维丛的推广。",
          "url": "blog/john-lee/vector-bundles.html"
        },
        {
          "title": "余切向量场",
          "description": "第 11 章：余向量与对偶空间、余切丛与余标架、函数微分、拉回与限制、线积分，以及闭形式与庞加莱引理。",
          "url": "blog/john-lee/covector-fields.html"
        },
        {
          "title": "张量",
          "description": "第 12 章：多线性映射与张量积、协变与逆变张量、对称与交替张量、张量丛与张量场、拉回与李导数。",
          "url": "blog/john-lee/tensors.html"
        },
        {
          "title": "微分形式运算法则",
          "description": "微分形式速查表：楔积、外微分、拉回、内乘与李导数的基本公式，以及常用恒等式汇总。",
          "url": "blog/john-lee/differential-forms.html"
        },
        {
          "title": "Hodge 算子、Laplace 算子与梯度散度旋度",
          "description": "体积元与 Hodge 星算子、外微分与拉回、向量场与 1-形式的同构，梯度、散度、旋度、Laplace 及习题恒等式。",
          "url": "blog/john-lee/hodge-laplace-operators.html"
        }
      ]
    }
  ],
  // --- END 专题 ---
  publications: [],
  experience: [],
  awards: [],
  interests: [],
  contact: {
    heading: "很高兴，在这里遇见你。",
    description: "关于学习、作品，或任何有趣的想法，都欢迎交流。"
  }
};

// --- BEGIN 优化专题：由 build_blog.py 生成，请勿手工改动 ---
// 插到数组最前面：主页上的专题顺序为「优化」→ John Lee
window.HOMEPAGE.topics = [
  {
    "title": "优化",
    "english": "OPTIMIZATION",
    "description": "从随机梯度的噪声几何、预训练中的球面动力学，到学习率无关的锥提升方法，收录 3 篇关于优化器与学习率的专题文章。",
    "url": "blog/optimization/index.html",
    "notes": [
      {
        "title": "优化器究竟在选择什么？",
        "description": "从随机梯度的稳定性与噪声几何出发，理解优化器如何影响模型的解与参数表示。",
        "url": "blog/sgd-noise-geometry.html"
      },
      {
        "title": "球面动力学、学习率与权重衰减",
        "description": "从尺度不变性与球面更新出发，串联有效学习率、Hyperball、权重衰减平衡、河谷动力学，以及预训练优化器的比较口径。",
        "url": "blog/pretraining-optimization-lecture.html"
      },
      {
        "title": "Schedule-Free学习率优化方法",
        "description": "从在线遗憾与锥提升出发，理解二次正则的尺度不变性、CBA / CBA+ 的投影更新，以及无界域中由 KT coin-betting 给出的学习率自适应。",
        "url": "blog/conic-lifting-blog.html"
      }
    ]
  },
  ...(window.HOMEPAGE.topics || []).filter(t => t.title !== "优化")
];
// --- END 优化专题 ---
