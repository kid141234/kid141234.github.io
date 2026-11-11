# 学习率不存在了？

传统梯度法里的学习率决定一步走多远。*Conic-Lifting for Learning-rate-free Convex Optimization* 把每个决策表示成一条射线。在论文的有界域构造里，学习率只影响算法在射线上的位置，实际决策由射线的方向决定。这个几何变化既解释了二次正则该怎么选，也把在线学习中的 Blackwell 算法和 coin-betting 放进了同一个框架。[论文原文][paper]

标题里的“消失”有一个具体的含义。在有界闭凸域的 Hilbert 空间构造中，用二次正则做锥上的 FTRL，把一个固定的正学习率换成另一个，只会沿射线缩放算法状态，解码后的决策序列完全相同。这是凸优化中一套更新规则的性质。推广到无界域时，还要保证锥坐标能解码，并说明算法用什么控制梯度尺度。 [\[1\]](#src-1)

## 1. 学习率原本在平衡什么？

先想象一个只能边做边看的问题。第 $t$ 轮，你先在非空闭凸集 $\mathcal V$ 中选 $x_t$，然后才收到凸损失 $\ell_t$ 在这个点的次梯度 $g_t$。跑完 $T$ 轮，回过头问，如果每轮都坚持用同一个点 $u$，表现会怎样？把每轮的损失差用一阶项来量，就得到线性化遗憾（regret）。

$$
\operatorname{Reg}_T(u)=\sum_{t=1}^{T}\langle g_t,x_t-u\rangle.
$$

凸性给出 $\ell_t(x_t)-\ell_t(u)\le\langle g_t,x_t-u\rangle$，因此这个和上界了实际累计损失差。算法要在看见本轮反馈前选 $x_t$，比较点 $u$ 可以等到结束再定，比如选整段累计损失最低的固定点。这处时间上的区别，后面会派上用场。 [\[1\]](#src-1)

在实 Hilbert 空间里，记范数为 $\|\cdot\|_2$。假设 $R>0$，并且 $\mathcal V$ 里的点都满足 $\|x\|_2\le R$。先试最直接的办法，在原空间里用二次正则 $\|x\|_2^2/(2\eta)$ 做 FTRL（跟随正则化领导者）。取 $\eta>0$，它给出两项代价。

$$
\operatorname{Reg}_T(u)
\le
\underbrace{\frac{R^2}{2\eta}}_{\text{比较点的正则化代价}}
+
\underbrace{\frac{\eta}{2}\sum_{t=1}^{T}\|g_t\|_2^2}_{\text{算法对新梯度的响应代价}}.
$$

如果 $\eta$ 太小，第一项就大。如果 $\eta$ 太大，历史梯度越强，第二项就长得越快。手里若有完整的 $S_T=\sum_{t=1}^T\|g_t\|_2^2>0$，取 $\eta=R/\sqrt{S_T}$，两项便一样大。

可在真正开始时，$S_T$ 还没有发生。刚才唯一允许事后选择的是比较点。能否给同一个 $u$ 多几种表示，让证明在事后选其中一种，从而也能平衡这两项？ [\[1\]](#src-1)

## 2. 从相对损失到锥空间

先看第 $t$ 轮的比较。已经选了 $x_t$，若换成另一个点 $x$，一阶损失会变多少？以 $x_t$ 为基准，写成

$$
d_t(x)=\langle g_t,x-x_t\rangle
=\langle g_t,x\rangle+b_t,
\qquad
b_t=-\langle g_t,x_t\rangle.
$$

麻烦在于右边有个截距 $b_t$。给 $x$ 添一维，写成 $(x,1)$，就可以把截距放进同一个内积。再把这个坐标整体乘上 $s>0$，记 $y=sx$。如果原来的决策要靠 $y/s$ 恢复，那么与它对应的损失也乘上 $s$，恰好得到

$$
s\,d_t(y/s)
=\langle g_t,y\rangle+b_t s
=\langle\widehat g_t,(y,s)\rangle,
\qquad
\widehat g_t=(g_t,b_t).
$$

这和齐次坐标的用法很像。同一条射线上的 $(sx,s)$ 都代表 $x$，但用内积计算时，高度 $s$ 会留下来。于是我们可以让算法在凸锥 $\mathcal C_{\mathcal V}=\{s(x,1):x\in\mathcal V,\ s\ge0\}$ 上维护 $z_t=(y_t,s_t)$。高度为正时读出 $x_t=y_t/s_t$，有界域的锥在高度为零时只剩原点，此时采用预先指定的默认决策。

这里可以做一次小检查。拿当前决策和自己比，$d_t(x_t)=0$，所以 $\langle\widehat g_t,z_t\rangle=0$，在原点也成立。现在把同一个比较点 $u$ 放在任意高度 $\lambda>0$，一轮的锥上遗憾就变成

$$
\langle\widehat g_t,z_t-\lambda(u,1)\rangle
=\lambda\langle g_t,x_t-u\rangle.
$$

取 $x_t=1/2$、$g_t=2$、$u=-1/2$ 试试。原空间的遗憾是 $2$。锥上反馈为 $(2,-1)$，与代表 $x_t$ 的 $(1,2)$ 做内积得零。把 $u$ 放在高度 $3$，也就是 $(-3/2,3)$，遗憾变成 $6$。读回原空间，比较的还是同一个 $-1/2$。逐轮累加 $-\widehat g_t$ 也就是带常数坐标的拉格朗日对冲里的遗憾向量，这给出了与 Blackwell 可逼近性的联系。 [\[1\]](#src-1) [\[2\]](#src-2)

## 3. 二次正则怎样把学习率吸收到尺度里？

比较点可以挑高度了。算法自己的状态呢？如果改动 FTRL 的学习率，会不会连它选中的射线也一起改变？

先给横向坐标和高度分别计二次代价，用一个 $\alpha>0$ 调节高度的权重。

$$
\psi_\alpha(y,s)=\frac12\big(\|y\|_2^2+\alpha s^2\big),
\qquad \alpha>0.
$$

记累计提升反馈为 $H_{t-1}=\sum_{i<t}\widehat g_i$。锥上的 FTRL 最小化 $\psi_\alpha(z)/\eta+\langle H_{t-1},z\rangle$。试着把状态写成 $z=\eta w$。锥允许沿射线缩放，所以 $w$ 仍然遍历同一个锥。目标函数此时变为

$$
\frac1\eta\psi_\alpha(\eta w)+\langle H_{t-1},\eta w\rangle
=\eta\big[\psi_\alpha(w)+\langle H_{t-1},w\rangle\big].
$$

二次项原来除以 $\eta$，换元后留下一个 $\eta$。线性项也乘上同一个 $\eta$。这个正因子不会改变 $w$ 的最优点，于是同一段累计反馈下，$z_t^{(\eta)}=\eta z_t^{(1)}$。正高度时分子与分母一起缩放，读出来的 $x_t$ 一样。若两边都在原点，就采用同一个默认决策。下一轮收到的反馈也相同，因此从相同初始化开始，这个关系可以逐轮递推。 [\[1\]](#src-1)

还可以只盯着一条射线算一遍。固定 $x$，记 $D(x)=\|x\|_2^2+\alpha$、$L_t(x)=\langle H_{t-1},(x,1)\rangle$。沿 $z=s(x,1)$ 的目标为 $s^2D(x)/(2\eta)+sL_t(x)$。先求这个一维二次式的最小点，再用 $s\ge0$ 截住它，就得到

$$
s^\star(x)=\frac{\eta[-L_t(x)]_+}{D(x)},
\qquad [a]_+=\max\{a,0\}.
$$

代回去，最小值为 $-\eta[-L_t(x)]_+^2/(2D(x))$。换 $\eta$ 会拉伸每条射线的最优高度，但射线之间比较的是被同倍放大的值。实现里因此可以取 $\eta=1$。此时仍有一个值得选的量，$\alpha$ 会改变不同 $x$ 的 $D(x)$，从而改变射线之间的比较。

## 4. 为什么高度的权重恰好是 $R^2$？

第 1 节想借比较点平衡两项代价。现在可以把这个想法用在锥上，顺便看高度的权重怎样影响最后的界。

记 $\|z\|_\alpha^2=\|y\|_2^2+\alpha s^2$。高度在原范数里乘了 $\alpha$，反馈的最后一维在对偶范数里便除以 $\alpha$，即 $\|(g,b)\|_{\alpha,*}^2=\|g\|_2^2+b^2/\alpha$。把二次正则的 FTRL 上界搬到这套度量里，对锥中任意比较状态 $v$ 有

$$
\sum_{t=1}^{T}\langle\widehat g_t,z_t-v\rangle
\le
\frac{\|v\|_\alpha^2}{2\eta}
+\frac{\eta}{2}\sum_{t=1}^{T}\|\widehat g_t\|_{\alpha,*}^2.
$$

取 $v=\lambda(u,1)$。右边第一项含 $\lambda^2$，左边按第 2 节的恒等式含一个 $\lambda$。除以它，并记 $A=\|(u,1)\|_\alpha^2$、$B=\sum_{t=1}^T\|\widehat g_t\|_{\alpha,*}^2$，就得到

$$
\operatorname{Reg}_T(u)
\le \frac{\lambda}{2\eta}A+\frac{\eta}{2\lambda}B.
$$

把 $\eta/\lambda$ 当成一个数看，这就是开头的两项权衡。$\eta$ 已经固定，$\lambda$ 还可以选。若 $B>0$，取 $\lambda=\eta\sqrt{B/A}$ 让两项相等，遗憾至多为 $\sqrt{AB}$。若 $B=0$，让 $\lambda\downarrow0$ 得到同一个下确界。用到未来梯度的是比较状态的选取，这一步发生在分析里。 [\[1\]](#src-1)

接着估计 $\sqrt{AB}$。因为 $\|u\|_2\le R$，所以 $A\le R^2+\alpha$。又因为 $b_t=-\langle g_t,x_t\rangle$ 且 $\|x_t\|_2\le R$，所以 $B\le(1+R^2/\alpha)S_T$。如果把 $\alpha$ 调大，比较点更贵，反馈的最后一维却更便宜。令上界写成 $C(\alpha)\sqrt{S_T}$，要平衡的就是

$$
C(\alpha)^2=(R^2+\alpha)\left(1+\frac{R^2}{\alpha}\right)
=2R^2+\alpha+\frac{R^4}{\alpha}.
$$

最后两项的乘积固定为 $R^4$，它们相等时和最小。因此 $\alpha=R^2$，得到

$$
\psi(y,s)=\frac12\big(\|y\|_2^2+R^2s^2\big)
\qquad\Longrightarrow\qquad
\operatorname{Reg}_T(u)\le 2R\sqrt{S_T}.
$$

从锥的形状也能看出为什么是这个量级。高度 $s$ 的截面上，横向坐标满足 $\|y\|_2\le Rs$。在正则里用 $Rs$ 度量高度，正好与这一截面的横向尺度相配。 [\[1\]](#src-1)

这个 $2$ 还有一个可以检验的意义。AdaGrad-Norm 的相应上界为 $2\sqrt2 R\sqrt{S_T}$。即使可行域只有一维的 $[-R,R]$，若算法事先既不知道梯度上界也不知道总轮数，要对所有轮数、比较点和梯度序列统一保证 $\mathbb E[\operatorname{Reg}_T(u)]\le cR\sqrt{S_T}$，就需要 $c\ge2$。这里的期望取自算法内部的随机性，梯度序列可以各自有一个有限但未知的上界。比较的是这些条件下的最坏情形常数。 [\[1\]](#src-1)

## 5. 同一个构造怎样变成三类算法？

### 有界域上的 CBA 和 CBA+

有了 $\alpha=R^2$，每轮最小化要怎么算？把最后一维的权重吸收到梯度里，记 $h_t=(g_t,b_t/R^2)$，用 $\Pi_{\mathcal C_{\mathcal V}}^{R}$ 表示按 $\|\cdot\|_{R^2}$ 做的投影。对 FTRL 目标配方，就会出现离 $-\sum_{i=1}^th_i$ 最近的锥中点，这给出锥 Blackwell 算法（CBA）。也可以从已经投影好的状态出发，只减本轮的 $h_t$ 再投影，这就是在同一个锥上做在线镜像下降的 CBA+。

$$
z_{t+1}^{\mathrm{CBA}}
=\Pi_{\mathcal C_{\mathcal V}}^{R}\!\left(-\sum_{i=1}^{t}h_i\right),
\qquad
z_{t+1}^{\mathrm{CBA+}}
=\Pi_{\mathcal C_{\mathcal V}}^{R}(z_t^{\mathrm{CBA+}}-h_t).
$$

把这两行各走两步，区别就很清楚。CBA 一直保留未投影的累计反馈，CBA+ 把每轮的投影结果带进下一轮。它们各用自己解码出的 $x_t$ 生成反馈。若在有限维非欧氏空间里有强凸的平方范数，同一思路还可以用相应的正则目标和镜像更新实现。 [\[1\]](#src-1)

### 无界域、已知梯度上界时的 KT coin-betting

刚才选 $R^2$ 用到了有限的截面大小。若 $\mathcal V=\mathbb R$，试着取锥中一列点 $(1,1/n)$，它们解码为 $n$，极限 $(1,0)$ 却无法解码。无界域里还得解决一件事，更新后怎样保证 $s$ 严格为正？

取一个可行点 $a\in\mathcal V$ 作锚，把原决策平移为 $x-a$。在 $\mathcal C_{\mathcal V-a}$ 上要求 $s>0$，加入 $\epsilon(s-\ln s)$。靠近零时，$-\ln s$ 会把代价推高。这里 $\epsilon>0$ 还设定了相对锚点的遗憾预算。若已知对偶范数下的梯度上界 $\|g_t\|_*\le G$，其中 $G>0$，第 $t$ 轮可将历史提升损失和下面的正则一起最小化。

$$
\frac{\beta G^2t}{2\epsilon}\|y\|^2+\epsilon(s-\ln s).
$$

反馈的最后一维相应变成 $-\langle g_t,x_t-a\rangle$。在实 Hilbert 空间或平方范数强凸的有限维实赋范空间中，对非空闭凸域取 $\beta\ge2$，可保证更新存在且高度始终为正。界随比较点到锚的距离变化，量级为 $\epsilon+\widetilde O(G\|u-a\|\sqrt T)$，其中 $\widetilde O$ 省略对数因子。一般闭凸域上的 Hilbert 空间实现可以先固定高度，投影到该高度的横截面，再用一维求根确定高度。 [\[1\]](#src-1)

如果可行域就是整个 Hilbert 空间，给定任意正高度，$y$ 仍可自由取值。这样就能把横向与高度两个最小化问题分开。取这个特例对应的 $\beta=1$，令 $S_{t-1}^{\mathrm{vec}}=\sum_{i<t}g_i$，将高度的一次项系数记成

$$
W_t=\epsilon-\sum_{i<t}\langle g_i,x_i-a\rangle.
$$

高度的目标是 $W_ts-\epsilon\ln s$。在已知 $G$ 的这个特例中有 $W_t>0$，令导数为零即可解出高度。横向目标是二次式，最小点为 $y_t=-\epsilon S_{t-1}^{\mathrm{vec}}/(G^2t)$。再做一次 $y_t/s_t$，得到原空间的更新。

$$
s_t=\frac{\epsilon}{W_t},
\qquad
x_t-a=-\frac{W_t}{G^2t}S_{t-1}^{\mathrm{vec}}.
$$

若把 $-g_t/G$ 当作每轮回报，$W_t/G$ 就是财富，$x_t-a$ 是下注向量。累积梯度决定方向，财富决定下注多少。这和 Krichevsky–Trofimov（KT）coin-betting 的逐轮更新相同。从锥上看，财富越多，高度越小，同一横向坐标解码出的步子也就越大。 [\[1\]](#src-1)

### 无约束、梯度上界未知时的自适应版本

上一步把 $G^2t$ 放进了横向正则。如果连 $G$ 也不知道，能从已经见过的梯度里读到哪些尺度？在无约束情形取原点为锚，记 $m_0=0$。每轮结束后可以同时记下最大范数、累计平方范数，以及最大范数每次刷新时的跳幅平方。

$$
m_t=\max_{1\le i\le t}\|g_i\|_*,
\qquad
v_t=\sum_{i=1}^{t}\|g_i\|_*^2,
\qquad
\delta_t=\sum_{i=1}^{t}(m_i-m_{i-1})^2.
$$

例如最大范数直接从 $0$ 跳到 $10$，$\delta_t=100$。若逐轮经过 $1,2,\ldots,10$，每次只增加 $1$，$\delta_t=10$。虽然最终的 $m_t$ 一样，这第三个量会对突然出现的大梯度给出更高的代价。 [\[1\]](#src-1)

这些历史统计用来调整下一轮的正则和 $\|y\|$ 上限。若一个决策 $x$ 看起来需要很大的 $y$，只要沿它的射线选足够小的正高度，就仍能把它表示出来。实际更新使用完整梯度，分析用 $\delta_T$ 衡量超过历史尺度的代价。这个版本还有初始预算 $\epsilon$ 和权衡参数 $\gamma>0$。若平方范数的一半的强凸常数为 $\mu$，增大 $\gamma$ 会减小 $\delta_T/(2\mu\gamma)$，同时抬高远处比较点的代价 $\gamma\|u\|^2/2$。 [\[1\]](#src-1)

## 6. 对训练优化意味着什么？

在线遗憾比较的是一整串决策。若我们的目标是最小化同一个凸函数 $f$，怎样把这串决策变成一个有误差保证的点？设 $x_t$ 由历史信息 $\mathcal F_{t-1}$ 决定，观测满足 $\mathbb E[g_t\mid\mathcal F_{t-1}]\in\partial f(x_t)$。对固定的 $u\in\mathcal V$，先用条件无偏性和次梯度不等式得到

$$
\mathbb E[f(x_t)-f(u)]
\le \mathbb E[\langle g_t,x_t-u\rangle].
$$

求和以后，右边就是遗憾。左边则可以借助凸性换成平均迭代点 $\bar x_T=T^{-1}\sum_{t=1}^Tx_t$ 的损失，从而有

$$
\mathbb E[f(\bar x_T)-f(u)]
\le \frac{\mathbb E[\operatorname{Reg}_T(u)]}{T}.
$$

例如在第 4 节的有界 Hilbert 空间设定下，若 $\|g_t\|_2\le G$，就有 $S_T\le TG^2$。代入 CBA 的遗憾界，平均点的期望次优性至多为 $2RG/\sqrt T$。这个结论用到了凸性、条件无偏次梯度、有界域和梯度范数控制。计算成本也随版本而异，有界域要做锥投影，一般闭凸约束的正高度版本还需求根，无约束且已知 $G$ 的 KT 特例则有闭式更新。 [\[1\]](#src-1)

如果目标换成深度网络中的非凸损失，从梯度内积控制损失差、再从逐轮损失换到平均点，这两步都需要新的依据。对应的更新能否带来训练收益，要看非凸情形的分析与实验。

## 参考文献

1. <span id="src-1"></span> Grand-Clément、Kwon、Orabona（2026）。*Conic-Lifting for Learning-rate-free Convex Optimization*. §2–3 给出在线优化设定与锥提升，§5–6 讨论有界域，§7–8 讨论已知和未知梯度上界的情形。 [arXiv:2610.39531v1](https://arxiv.org/abs/2610.39531v1) · [HTML 全文](https://arxiv.org/html/2610.39531v1)
2. <span id="src-2"></span> Gordon（2006）。*No-regret Algorithms for Online Convex Programs*. §3 给出拉格朗日对冲的遗憾向量与常数坐标。 [论文全文](https://papers.nips.cc/paper_files/paper/2006/file/f14bc21be7eaeed046fed206a492e652-Paper.pdf)

[paper]: https://arxiv.org/abs/2610.39531v1
