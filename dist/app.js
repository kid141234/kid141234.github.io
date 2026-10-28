(() => {
  "use strict";
  const data = window.HOMEPAGE || {};
  const profile = data.profile || {};
  const text = value => value == null ? "" : String(value).trim();
  const esc = value => text(value).replace(/[&<>"']/g, char => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char]);
  const list = value => Array.isArray(value) ? value : [];
  const items = (value, key) => list(value).filter(item => item && typeof item === "object" && text(item[key]));
  const safeUrl = value => {
    const url = text(value);
    if (!url || /[\x00-\x20\\]/.test(url) || url.startsWith("//")) return "";
    if (/^[a-z][a-z\d+.-]*:/i.test(url)) {
      try { const parsed = new URL(url); return ["http:", "https:"].includes(parsed.protocol) ? url : ""; } catch { return ""; }
    }
    return url;
  };
  const paths = {
    school: '<path d="m3 10 9-6 9 6-9 6-9-6Z"/><path d="M6 12v6c3 3 9 3 12 0v-6M21 10v7"/>',
    book: '<path d="M12 6v15M3 4c4-1 7 0 9 2 2-2 5-3 9-2v15c-4-1-7 0-9 2-2-2-5-3-9-2V4Z"/>',
    pin: '<path d="M19 10c0 5-7 11-7 11S5 15 5 10a7 7 0 1 1 14 0Z"/><circle cx="12" cy="10" r="2"/>',
    mail: '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 6 9 7 9-7"/>',
    arrow: '<path d="M5 12h14m-5-5 5 5-5 5"/>',
    external: '<path d="M7 17 17 7M7 7h10v10"/>',
    github: '<path d="M9 19c-4 1-4-2-6-2m12 4v-3c0-1 .1-2-.5-2.5 3-.4 5.5-1.5 5.5-5.5 0-1.5-.5-2.5-1.5-3.5.2-1 .2-2-.2-3.2-2 0-3.3 1.2-3.3 1.2a12 12 0 0 0-6 0S7.7 3.3 5.7 3.3c-.4 1.2-.4 2.2-.2 3.2C4.5 7.5 4 8.5 4 10c0 4 2.5 5.1 5.5 5.5-.6.5-.5 1.5-.5 2.5v3"/>',
    link: '<path d="m10 13 4-4m-6 7-2 2a4 4 0 0 1-6-6l4-4a4 4 0 0 1 6 0m4 0 2-2a4 4 0 0 1 6 6l-4 4a4 4 0 0 1-6 0" transform="translate(1 0) scale(.95)"/>',
    folder: '<path d="M3 7a2 2 0 0 1 2-2h5l2 3h7a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7Z"/><path d="M8 14h8m-4-4v8"/>',
    camera: '<path d="M4 7h4l2-3h4l2 3h4a1 1 0 0 1 1 1v12H3V8a1 1 0 0 1 1-1Z"/><circle cx="12" cy="13" r="4"/><path d="M17 10h1"/>',
    compass: '<circle cx="12" cy="12" r="9"/><path d="m16 8-2 6-6 2 2-6 6-2Z"/>',
    award: '<circle cx="12" cy="8" r="5"/><path d="m8 12-2 9 6-3 6 3-2-9"/>',
    copy: '<rect x="8" y="8" width="12" height="13" rx="2"/><path d="M16 8V3H3v13h5"/>',
    download: '<path d="M12 3v12m-4-4 4 4 4-4M4 16v5h16v-5"/>'
  };
  const icon = name => `<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths[name] || paths.link}</svg>`;
  const links = value => items(value, "label").filter(item => safeUrl(item.url)).map(item => `<a href="${esc(safeUrl(item.url))}" target="_blank" rel="noopener noreferrer">${esc(item.label)}${icon("external")}</a>`).join("");
  const tags = value => list(value).filter(v => typeof v === "string" && v.trim()).map(v => `<span class="tag">${esc(v)}</span>`).join("");
  const name = text(profile.name) || "你的名字";
  const school = text(profile.school);
  const role = text(profile.role) || "学生";
  const email = /^[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+$/.test(text(profile.email)) ? text(profile.email) : "";
  const intro = data.intro || {};
  const profileLinks = items(profile.links, "label").filter(item => safeUrl(item.url));
  const detail = (name, value) => `<div class="profile-detail">${icon(name)}<span>${esc(value)}</span></div>`;
  document.getElementById("profile").innerHTML = `
    <div class="avatar-wrap"><img class="avatar" src="${esc(safeUrl(profile.avatar) || "assets/avatar.svg")}" alt="${text(profile.avatar) ? esc(name) + "的头像" : "待替换头像：一株生长中的小树苗"}" width="142" height="142" data-avatar><span class="avatar-badge" aria-hidden="true">✳</span></div>
    <h2 class="profile-name">${esc(name)}</h2>
    <p class="profile-english">${esc(text(profile.englishName) || "YOUR NAME")}</p>
    <span class="role-pill"><span class="role-dot" aria-hidden="true"></span>${esc(role)}</span>
    <div class="profile-details">${detail("school", school || "院校待填写")}${detail("book", text(profile.major) || "专业待填写")}${text(profile.location) ? detail("pin", profile.location) : ""}</div>
    <div class="profile-line"></div><p class="profile-motto">${esc(intro.tagline || "保持好奇，慢慢积累。")}</p>
    <div class="profile-links">${email ? `<a href="mailto:${esc(email)}">${icon("mail")}<span>${esc(email)}</span></a>` : ""}${profileLinks.map(item => `<a href="${esc(safeUrl(item.url))}" target="_blank" rel="noopener noreferrer">${icon(item.icon)}<span>${esc(item.label)}</span></a>`).join("")}</div>
    <a class="sidebar-contact" href="#contact">联系我${icon("arrow")}</a>
    <p class="profile-footnote"><span aria-hidden="true">↗</span> LEARNING & GROWING</p>`;

  const sections = [];
  const add = (id, title, en, nav, body, extra = "") => sections.push({id, nav, html:`<section class="section ${extra}" id="${id}" aria-labelledby="${id}-title"><div class="section-heading"><div class="section-title"><h2 id="${id}-title">${title}</h2><span class="section-en">${en}</span></div><span class="section-index" aria-hidden="true">${String(sections.length).padStart(2, "0")}</span></div>${body}</section>`});
  const focus = list(data.focus).filter(item => typeof item === "string" && item.trim());
  const about = list(data.about).filter(item => typeof item === "string" && item.trim());
  sections.push({id:"about", nav:"关于", html:`<section class="section about-section" id="about" aria-labelledby="about-title">
    <p class="eyebrow">ABOUT ME / 关于我</p>
    <h1 class="hero-title" id="about-title">${esc(intro.greeting || "你好，我是")}<span class="name">${esc(name)}</span>。</h1>
    <p class="hero-description">${esc(intro.description)}</p>
    <div class="about-copy">${about.length ? about.map(p => `<p>${esc(p)}</p>`).join("") : '<p class="placeholder-copy">个人介绍待填写。<br>可以从你的专业、正在学习的事，以及想探索的方向开始。</p>'}</div>
    <div class="hero-facts"><div><span class="fact-label">目前身份</span><span class="fact-value">${esc(role)}</span></div><div><span class="fact-label">所在院校</span><span class="fact-value${school ? "" : " empty"}">${esc(school || "待填写")}</span></div><div><span class="fact-label">关注方向</span><span class="fact-value${focus.length ? "" : " empty"}">${esc(focus.length ? focus.join(" / ") : "待探索，待记录")}</span></div></div>
  </section>`});

  const timelineItem = (item, heading, subtitle) => `<article class="timeline-item"><div class="entry-heading"><h3>${esc(heading)}</h3>${text(item.period) ? `<span class="entry-time">${esc(item.period)}</span>` : ""}</div>${subtitle ? `<p class="entry-subtitle">${esc(subtitle)}</p>` : ""}${text(item.description) ? `<p class="entry-description">${esc(item.description)}</p>` : ""}</article>`;
  const education = items(data.education, "school");
  add("education", "教育经历", "EDUCATION", "教育", `<div class="timeline">${education.length ? education.map(item => timelineItem(item, item.school, [item.major, item.degree].filter(Boolean).join(" · "))).join("") : '<article class="timeline-item is-placeholder"><div class="entry-heading"><h3>学校名称<span class="placeholder-label">待填写</span></h3><span class="entry-time">入学年份 — 毕业年份</span></div><p class="entry-subtitle">专业 · 学位</p><p class="entry-description">在这里记录你的学习经历。</p></article>'}</div>`);

  const projects = items(data.projects, "title");
  add("projects", "项目与作品", "SELECTED WORK", "作品", projects.length ? `<div class="project-list">${projects.map(item => {
    const img = safeUrl(item.image);
    return `<article class="project${img ? " with-image" : ""}">${img ? `<img class="project-image" src="${esc(img)}" alt="${esc(item.imageAlt || item.title)}" loading="lazy" data-image>` : ""}<div>${text(item.date) ? `<div class="project-date">${esc(item.date)}</div>` : ""}<h3>${esc(item.title)}</h3>${text(item.description) ? `<p>${esc(item.description)}</p>` : ""}${list(item.tags).length ? `<div class="focus-tags">${tags(item.tags)}</div>` : ""}${links(item.links) ? `<div class="entry-links">${links(item.links)}</div>` : ""}</div></article>`;
  }).join("")}</div>` : `<div class="empty-project"><div class="empty-art">${icon("folder")}</div><div><h3>下一件作品，从这里开始。</h3><p>课程项目、个人开发，或一次有趣的尝试。</p><span class="empty-project-label">作品待添加</span></div></div>`);

  const publications = items(data.publications, "title");
  if (publications.length) add("publications", "论文发表", "PUBLICATIONS", "论文", publications.map(item => `<article class="publication"><h3>${esc(item.title)}</h3>${text(item.authors) ? `<p class="publication-authors">${esc(item.authors)}</p>` : ""}${item.venue || item.year ? `<p class="publication-venue">${esc([item.venue, item.year].filter(Boolean).join(" · "))}</p>` : ""}${links(item.links) ? `<div class="entry-links">${links(item.links)}</div>` : ""}</article>`).join(""));

  const experience = items(data.experience, "organization");
  if (experience.length) add("experience", "实习与实践", "EXPERIENCE", "实践", `<div class="timeline">${experience.map(item => timelineItem(item, item.organization, item.role)).join("")}</div>`);
  const awards = items(data.awards, "title");
  if (awards.length) add("awards", "荣誉奖项", "HONORS & AWARDS", "荣誉", `<div class="awards-list">${awards.map(item => `<article class="award">${icon("award")}<div class="award-content"><div class="entry-heading"><h3>${esc(item.title)}</h3>${text(item.date) ? `<span class="entry-time">${esc(item.date)}</span>` : ""}</div>${text(item.organization) ? `<p class="entry-subtitle">${esc(item.organization)}</p>` : ""}</div></article>`).join("")}</div>`);

  const interests = items(data.interests, "title");
  const placeholderInterests = [
    {title:"一段日常", description:"放一张照片，记录一个瞬间。", icon:"camera"},
    {title:"一个爱好", description:"写写让你投入其中的小事。", icon:"compass"},
    {title:"一份灵感", description:"分享一本书，或一些想法。", icon:"book"}
  ];
  add("life", "生活与兴趣", "BEYOND STUDY", "生活", `<p class="section-intro">学习之外，也给喜欢的事留一点空间。</p><div class="interest-grid">${(interests.length ? interests : placeholderInterests).map(item => `<article class="interest${interests.length ? "" : " interest-placeholder"}"><div class="interest-picture">${icon(item.icon || "compass")}${safeUrl(item.image) ? `<img src="${esc(safeUrl(item.image))}" alt="${esc(item.imageAlt || item.title)}" loading="lazy" data-image>` : ""}</div><h3>${esc(item.title)}</h3><p>${esc(item.description)}</p>${interests.length ? (safeUrl(item.url) ? `<div class="entry-links"><a href="${esc(safeUrl(item.url))}" target="_blank" rel="noopener noreferrer">了解更多${icon("external")}</a></div>` : "") : '<div class="interest-meta">待填写 / TO BE ADDED</div>'}</article>`).join("")}</div>`);

  const contact = data.contact || {};
  const resume = safeUrl(profile.resume);
  sections.push({id:"contact", nav:"联系", html:`<section class="section contact-section" id="contact" aria-labelledby="contact-title"><div class="contact-box"><h2 id="contact-title">${esc(contact.heading || "很高兴，在这里遇见你。")}</h2><p>${esc(contact.description)}</p><div class="contact-actions">${email ? `<a class="email-link" href="mailto:${esc(email)}">${icon("mail")}${esc(email)}</a><button class="copy-email" id="copy-email" type="button">${icon("copy")}复制邮箱</button>` : `<span class="contact-placeholder">${icon("mail")}联系邮箱待填写</span>`}${resume ? `<a class="resume-link" href="${esc(resume)}" target="_blank" rel="noopener noreferrer">${icon("download")}查看简历</a>` : ""}</div>${profileLinks.length ? `<div class="entry-links contact-socials">${links(profileLinks)}</div>` : ""}</div></section>`});

  document.getElementById("main").innerHTML = sections.map(section => section.html).join("");
  document.getElementById("navigation").innerHTML = sections.map(section => `<a href="#${section.id}"${section.id === "about" ? ' aria-current="location"' : ""}>${section.nav}</a>`).join("");
  document.title = text(profile.name) ? `${text(profile.name)} · 个人主页` : "个人主页 · 学习与生活";
  document.querySelector('meta[name="description"]').content = text(intro.description) || "个人主页，记录学习、作品与生活。";
  document.getElementById("copyright").textContent = `© ${new Date().getFullYear()} ${name} · Personal Homepage`;

  document.querySelector("[data-avatar]").addEventListener("error", event => {
    event.target.src = "assets/avatar.svg";
    event.target.alt = "头像加载失败，显示默认小树苗插画";
  }, {once:true});
  document.querySelectorAll("[data-image]").forEach(img => img.addEventListener("error", () => {
    img.closest(".project")?.classList.remove("with-image");
    img.remove();
  }, {once:true}));

  let toastTimer;
  const showToast = message => {
    const toast = document.getElementById("toast");
    clearTimeout(toastTimer);
    toast.textContent = message;
    toast.classList.add("visible");
    toastTimer = setTimeout(() => toast.classList.remove("visible"), 3500);
  };
  document.getElementById("copy-email")?.addEventListener("click", async () => {
    try { await navigator.clipboard.writeText(email); showToast("邮箱已复制，期待你的来信。"); }
    catch { showToast("复制未成功，请选择页面上的邮箱地址手动复制。"); }
  });

  const navLinks = [...document.querySelectorAll("#navigation a")];
  const sectionElements = sections.map(section => document.getElementById(section.id));
  let scheduled = false;
  function updateNav() {
    const offset = document.querySelector(".site-header").offsetHeight + 120;
    let current = sectionElements[0];
    for (const section of sectionElements) if (section.getBoundingClientRect().top <= offset) current = section;
    if (Math.ceil(window.innerHeight + window.scrollY) >= document.documentElement.scrollHeight - 3) current = sectionElements.at(-1);
    navLinks.forEach(link => {
      if (link.getAttribute("href") === `#${current.id}`) link.setAttribute("aria-current", "location");
      else link.removeAttribute("aria-current");
    });
    scheduled = false;
  }
  window.addEventListener("scroll", () => { if (!scheduled) { scheduled = true; requestAnimationFrame(updateNav); } }, {passive:true});
  window.addEventListener("resize", updateNav, {passive:true});
  updateNav();
  if (location.hash) requestAnimationFrame(() => {
    const target = document.getElementById(location.hash.slice(1));
    if (target) target.scrollIntoView();
  });
})();
