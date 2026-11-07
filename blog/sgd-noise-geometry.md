

# 优化器究竟在选择什么？

神经网络训练并不只有“把训练损失降下来”这一个问题。过参数化模型往往有很多训练误差相同的解，但不同优化器、学习率、batch size 和初始化，最后会得到不同的参数，甚至不同的测试性能。

本文围绕一个问题展开：**当训练误差已经很低时，更新规则还在筛选什么、推动什么？**

从随机梯度的基本性质出发，我们将依次讨论稳定性、噪声方向、函数复杂度和参数尺度，最后看看自适应优化器带来的新现象。

## 预备知识

记训练集大小为 $n$，参数维数为 $p$，输入维数为 $d$。经验损失为

$$
L(\theta)=\frac1n\sum_{i=1}^n\ell_i(\theta).
$$

定义全梯度 $b(\theta)=\nabla L(\theta)$，单样本梯度 $s_i(\theta)=\nabla\ell_i(\theta)$。单样本梯度的二阶矩与中心化协方差分别是

$$
M(\theta)=\frac1n\sum_i s_i s_i^\top,
\qquad
\Sigma(\theta)=M(\theta)-b(\theta)b(\theta)^\top.
$$

二者不可互换：$M$ 包含平均梯度，$\Sigma$ 才衡量围绕平均梯度的随机波动。

若一个 batch 内独立、有放回地抽取 $B$ 个样本，则

$$
\widehat g_B=b+\xi_B,
\qquad \mathbb E[\xi_B\mid\theta]=0,
\qquad \operatorname{Cov}(\xi_B\mid\theta)=\frac{\Sigma(\theta)}B,
$$

$$
\theta_{t+1}=\theta_t-\eta\bigl(b(\theta_t)+\xi_{B,t}\bigr).
$$

若 batch 在有限数据集中无放回抽取，协方差因子变成

$$
\frac{n-B}{B(n-1)}.
$$

因此，在固定参数处，增大 batch 会减小抽样噪声。但这还没有描述噪声的方向，也没有描述参数变化后噪声本身如何变化。

这些公式把每个 $\ell_i$ 视为固定的单样本损失。Dropout、随机数据增强以及依赖整个 batch 的计算还会引入额外随机性或依赖关系，分析时需要另行计入。

要进一步讨论局部几何，需要区分 Hessian、Gauss–Newton 矩阵和梯度噪声。

先考虑标量输出的平方损失：

$$
\ell_i(\theta)=\frac12\bigl(f_\theta(x_i)-y_i\bigr)^2.
$$

令 $r_i=f_\theta(x_i)-y_i$，$g_i=\nabla_\theta f_\theta(x_i)$，则

$$
s_i=r_i g_i,
\qquad
G(\theta)=\frac1n\sum_i g_i g_i^\top,
$$

$$
H(\theta)=\nabla^2L(\theta)
=G(\theta)+\frac1n\sum_i r_i\nabla^2 f_\theta(x_i).
$$

这里 $G$ 是平方损失对应的 Gauss–Newton 矩阵，与梯度二阶矩 $M$ 是不同的对象。

在插值解 $\theta^*$ 处，所有 $r_i=0$，于是

$$
H(\theta^*)=G(\theta^*),\qquad
s_i(\theta^*)=0,\qquad \Sigma(\theta^*)=0.
$$

这解释了一个关键细节：**如果恰好位于零残差解，而且没有额外随机源，SGD 不会凭空产生噪声把自己推出去。稳定性分析研究的是受到一个小扰动之后会怎样。**

衡量局部曲率时，还需要区分几种不同的“尖锐度”。

在极小值附近，设 $H\succeq0$ 的特征值为 $\lambda_1\ge\cdots\ge\lambda_p\ge0$。

| 指标 | 公式 | 直观含义 |
|---|---|---|
| 最大特征值 | $\|\|H\|\|_2=\lambda_1$ | 最陡的那个方向 |
| Frobenius 范数 | $\|\|H\|\|_F=(\sum_i\lambda_i^2)^{1/2}$ | 各方向曲率的平方总量 |
| 迹 | $\operatorname{tr}H=\sum_i\lambda_i$ | 各方向曲率的总和 |

例如，$H_1=\operatorname{diag}(10,0,\ldots,0)$ 与 $H_2=10I_{100}$ 的最大特征值都为 10，但 Frobenius 范数分别为 10 和 100，迹分别为 10 和 1000。只看最大特征值，会遗漏很多“单个不更陡、合起来却很强”的方向。

后面的三种稳定性结论分别落在这三类指标上。它们不能脱离假设，直接比较成“后来的定理无条件更强”。

接下来比较连续梯度流和有限步长更新。

梯度流为 $\dot\theta=-\nabla L(\theta)$，GD 为 $\theta_{t+1}=\theta_t-\eta\nabla L(\theta_t)$。

对一维二次损失 $L(x)=\lambda x^2/2$，梯度流满足 $x(t)=e^{-\lambda t}x(0)$；GD 则满足

$$
x_{t+1}=(1-\eta\lambda)x_t.
$$

因此，GD 不放大小扰动要求 $|1-\eta\lambda|\le1$，即 $ 0\le \eta\lambda\le2$。端点可能只是不发散，严格收敛通常需要更严格的不等式。

学习率会改变哪些解能够稳定存在，而不仅是改变到达某个固定解的速度。接下来从局部稳定性出发，看看随机抽样如何改变这个条件。

在进入主要讨论前，还需要明确隐式正则化与稳定性的含义。

显式正则化会直接修改优化目标，例如最小化 $L(\theta)+\lambda R(\theta)$。隐式正则化则指：即使没有写出 $R$，更新规则仍对最终解产生结构性偏好，例如排除不稳定解、限制某种函数范数，或调整等价参数化的尺度。

这不意味着存在一个普适的隐藏惩罚项，使所有 SGD 轨迹都等价于对 $L+R$ 做梯度下降。后文分别讨论的是稳定性约束、噪声运动和参数平衡机制。

这里的**动态稳定性**关注参数受到小扰动后，训练动力学会收缩还是放大扰动。它与学习理论中“替换一个训练样本，输出变化多大”的**算法稳定性**是不同概念；两者不能仅因名称相似就直接互用结论。

## 稳定性与样本间的差异

在一个所有样本都达到极小值的点 $\theta^*$ 附近，令 $\delta=\theta-\theta^*$，并写成

$$
\ell_i(\theta^*+\delta)\approx\frac12\delta^\top H_i\delta,
\qquad H=\frac1n\sum_i H_i.
$$

GD 每步使用 $H$；SGD 每步使用随机抽出的 $H_i$ 或其 batch 平均值。因此，平均 Hessian 相同的两个问题，也可能具有不同的 SGD 动力学。

为了量化这种差异，定义

$$
V=\frac1n\sum_iH_i^2-H^2
=\frac1n\sum_i(H_i-H)^2,
$$

以及尖锐度 $a=\lambda_{\max}(H)$、非均匀性 $s=\sqrt{\lambda_{\max}(V)}$。$V$ 衡量各个样本对局部曲率的“意见分歧”。

**定理 1** [1]，按统一记号转述。对每步独立抽取、batch 内无放回的大小为 $B$ 的 SGD，如果

$$
\boxed{
\lambda_{\max}\left((I-\eta H)^2+
\eta^2\frac{n-B}{B(n-1)}V\right)\le1,
}
$$

那么线性化系统中的扰动二阶矩保持有界，因此该极小值线性稳定。**在一维中，这还是充要条件；一般高维中，这只是充分条件。**

这里的“线性稳定”是存在常数 $C$，使所有时刻满足 $\mathbb E\|\delta_t\|^2\le C\|\delta_0\|^2$。

定理左侧有两个来源：$(I-\eta H)^2$ 是平均下降动力学，第二项是随机曲率带来的额外放大。

一个一维例子可以说明样本差异为何重要。

考虑两个样本，损失为 $\ell_i(x)=a_i x^2/2$，每步抽一个样本。令 $a=\mathbb E a_i$，$s^2=\operatorname{Var}(a_i)$，则

$$
\mathbb E[x_{t+1}^2\mid x_t]
=\mathbb E[(1-\eta a_i)^2]x_t^2
=\bigl((1-\eta a)^2+\eta^2s^2\bigr)x_t^2.
$$

比较两组样本曲率：

| 样本曲率 | 平均曲率 $a$ | 非均匀性 $s$ | $\eta=1.5$ 时的二阶矩倍数 |
|---|---:|---:|---:|
| $(1,1)$ | 1 | 0 | 0.25 |
| $(0,2)$ | 1 | 1 | 2.5 |

它们的平均损失都是 $x^2/2$。第一组扰动收缩，第二组扰动的二阶矩指数增长。差别完全来自样本间曲率变化。

学习率和 batch size 不能只通过一个“噪声强度”参数概括。学习率同时改变平均动力学和随机项；batch 直接影响抽样项。保持 $\eta/B$ 不变，不意味着保持这个稳定性条件不变。

平均 Hessian 看起来安全，不代表小 batch 也安全。如果 GD 能稳定训练、小 batch SGD 却在同一位置剧烈波动，可以检查样本梯度或曲率是否存在强烈异质性。

这个机制解释了“筛选”，没有证明最优泛化。它排除某些不稳定解，但没有证明剩余解都很好，也没有证明 SGD 会到达某个指定的稳定解。

从上述矩阵条件还可以得到 $a\le2/\eta$ 和非均匀性的单独上界。需要注意逻辑方向：它们是上述充分判据成立的必要约束，不能直接升级为任意高维 SGD 线性稳定的完整刻画。

## 噪声的方向与曲率

把 SGD 的小步长近似写成随机微分方程

$$
d\theta_t=-\nabla L(\theta_t)\,dt+S(\theta_t)^{1/2}dW_t.
$$

这里用 $S$ 表示扩散协方差，以区别于前面的单样本梯度协方差 $\Sigma$。在时间取 $t=k\eta$ 的常见匹配中，$S\approx\eta\Sigma/B$。

由 Itô 公式，

$$
\boxed{
\frac{d}{dt}\mathbb E L(\theta_t)
=-\mathbb E\|\nabla L(\theta_t)\|^2
+\frac12\mathbb E\operatorname{tr}\bigl(H(\theta_t)S(\theta_t)\bigr).
}
$$

第一项降低损失；在 $H\succeq0$ 的局部区域，第二项衡量噪声向损失注入能量的速度。

如果 $H=\sum_i\lambda_i u_i u_i^\top$，那么

$$
\operatorname{tr}(HS)=\sum_i\lambda_i\,u_i^\top S u_i.
$$

同样的噪声方差，放在高曲率方向，造成的局部损失增长更大。

假设 $L(\theta)-L(0)=\theta^\top H\theta/2$，$H\succ0$，$S$ 为常矩阵，初始点为极小值 $\theta_0=0$。此时是 Ornstein–Uhlenbeck 过程，可以算出 [2]

$$
\boxed{
\mathbb E[L(\theta_t)-L(0)]
=\frac14\operatorname{tr}\bigl[(I-e^{-2Ht})S\bigr]
=\frac t2\operatorname{tr}(HS)+O(t^2).
}
$$

局部期望损失增长可以作为一种“逃离效率”指标。它不是完整非线性势阱的首次退出时间定理；事实上，在固定的正定二次模型中，上式长期会饱和。

**命题 1** [2] 的核心内容是：当 Hessian 的谱高度不均匀，并且噪声在高曲率方向有足够能量时，在固定 $\operatorname{tr}S$ 的公平比较下，它的局部损失注入量可以显著超过各向同性噪声。

可以用一个短不等式看清这个结论。设 $\overline S=(\operatorname{tr}S/p)I$，且

$$
u_1^\top S u_1\ge a\lambda_1\frac{\operatorname{tr}S}{\operatorname{tr}H},\qquad a>0.
$$

则

$$
\frac{\operatorname{tr}(HS)}{\operatorname{tr}(H\overline S)}
=\frac{p\operatorname{tr}(HS)}{\operatorname{tr}H\operatorname{tr}S}
\ge a p\frac{\lambda_1^2}{(\operatorname{tr}H)^2}.
$$

如果曲率集中在少数方向，右边就可能很大。极端例子是 $H=\operatorname{diag}(\lambda,0,\ldots,0)$：总方差相同，把噪声全部放在第一个方向，其损失注入量是各向同性噪声的 $p$ 倍。

**命题 2、3** [2] 进一步在特定单隐层网络中，建立梯度二阶矩、噪声协方差与 Hessian 的联系，为所需的对齐条件提供理论支持。其条件包括固定输出层、分段线性激活和特定裁剪输出设置，不能直接理解为任意神经网络都满足 $\Sigma=H$。

“GD 加一点高斯噪声”不自动等价于 SGD。即使两者的 $\mathbb E\|\xi\|^2$ 相同，其协方差方向也可以完全不同。

比较噪声方法时，应控制噪声总量，再比较方向。否则某种方法只是加了更多噪声，也可能被误判为噪声结构更好。

只记录梯度噪声的范数会漏掉机制。可以进一步估计噪声在 Hessian 主特征方向上的投影，或测量 $\operatorname{tr}(H\Sigma)$。

这说明噪声的几何结构很重要，但还不能据此断言所有各向异性噪声都会改善泛化。接下来把方向对齐和离散更新的稳定性联系起来。

## 噪声对齐与稳定性门槛

要把方向对齐与稳定性联系起来，还需要注意一个事实：**在平方损失插值问题中，噪声幅度会随残差、因而随损失一起变小。**

为刻画这一点，定义中心化噪声的对齐因子

$$
\mu(\theta)=\frac{\operatorname{tr}(\Sigma(\theta)G(\theta))}
{2L(\theta)\|G(\theta)\|_F^2}.
$$

所需条件是相关区域中 $\mu(\theta)\ge\mu_0>0$。这比要求整个矩阵严格满足 $\Sigma=2LG$ 更弱：只需要在影响损失增长的意义上，有足够强的对齐。

**定理 3.3** [3]。考虑插值极小值附近的线性化模型，使用独立抽样、batch size 为 $B$ 的 SGD。若噪声满足上述统一对齐下界，并且线性化系统的期望损失始终受初始期望损失的常数倍控制，则

$$
\boxed{
\|H(\theta^*)\|_F\le\frac1\eta\sqrt{\frac B{\mu_0}}.
}
$$

这是**必要条件**：超过门槛就不可能满足这里的损失稳定性；低于门槛，并不自动保证所有动态行为都稳定。

这个门槛中的 Frobenius 范数可以从一步更新中看出来。

线性化损失记作 $\mathcal L(\delta)=\delta^\top H\delta/2$。条件期望满足

$$
\mathbb E[\mathcal L(\delta_{t+1})\mid\delta_t]
=\mathcal L\bigl((I-\eta H)\delta_t\bigr)
+\frac{\eta^2}{2B}\operatorname{tr}\bigl(H\Sigma(\delta_t)\bigr).
$$

第一项非负。代入对齐条件得到

$$
\mathbb E\mathcal L(\delta_{t+1})
\ge q\,\mathbb E\mathcal L(\delta_t),
\qquad
q=\frac{\eta^2\mu_0}{B}\|H\|_F^2.
$$

如果 $q>1$，损失的期望就会指数增长。稳定性因此要求 $q\le1$。

当噪声在第 $i$ 个方向的方差与 $L\lambda_i$ 同阶时，该方向的损失注入还要再乘一次 $\lambda_i$，所以最终出现 $L\sum_i\lambda_i^2$。这就是 Frobenius 范数的来源。

**定理 3.5** [3]。在同样假设下，如果 $q>1$，那么

$$
\boxed{\mathbb E\mathcal L(\delta_t)\ge q^t\mathbb E\mathcal L(\delta_0).}
$$

严格结论针对线性化系统的期望损失。它不等于“每条随机轨迹都会以相同速度离开真实非线性势阱”，也不保证之后进入的区域有更好的测试性能。

这一对齐假设在线性模型和随机特征模型中有理论支持；对一般非线性网络，目前主要有实验支持。

大一点的学习率可以施加更严格的曲率筛选。同样的 $B$ 和对齐强度下，稳定解允许的 $\|H\|_F$ 上界与 $1/\eta$ 成正比。但继续增大到训练无法维持时，这种选择作用不再等于可用的训练收益。

固定学习率时，增大 batch 会放松这个筛选门槛。这为大 batch 与小 batch 最终选择不同解提供了一种机制，不是“大 batch 一定泛化更差”的定理。

平方根缩放有一个明确但有限的解释。如果只想保持这个局部阈值不变，并假设 $\mu_0$ 不变，则要保持 $\eta/\sqrt B$ 不变。这是关于该判据的比较，不是已经证明适用于所有任务的学习率缩放律。

更进一步，$\eta/B$ 控制常见 SDE 近似中的扩散强度，而 $\eta^2/B$ 出现在这里的离散放大系数中。两个比值描述不同对象，不应混为一谈。

## 从稳定性到函数复杂度

前面主要讨论哪些解稳定。如果要解释泛化，还需要建立

$$
\text{稳定性}\Longrightarrow\text{曲率约束}
\Longrightarrow\text{函数复杂度约束}
\Longrightarrow\text{测试风险上界}.
$$

在对角线性网络和两层 ReLU 网络中，可以具体建立这条链条。

先考虑 **$B=1$** 的 SGD。设

$$
Q_t=\mathbb E[\delta_t\delta_t^\top].
$$

其线性稳定性定义要求：对于任意初始扰动分布和任意 $t$，都有 $\|Q_t\|_F\le\|Q_0\|_F$。它与前面的期望损失有界定义不同。

**命题 3.2** [4]。在标量平方损失、零训练误差的设置下，如果极小值满足上述稳定性，那么

$$
\boxed{\operatorname{tr}H(\theta^*)\le\frac2\eta.}
$$

这个结果不需要前面的噪声对齐假设，但依赖这里的稳定性定义，以及零残差处单样本 Hessian 的秩一结构 $H_i=g_i g_i^\top$。

一个短证明。取 $Q_0=I$；由于系统线性，也可以把它整体缩小到任意局部尺度。于是

$$
Q_1=I-2\eta H+\eta^2\mathbb E_i[H_i^2].
$$

稳定性给出 $\|Q_1\|_F\le\sqrt p$，因此 $\operatorname{tr}Q_1\le\sqrt p\|Q_1\|_F\le p$，即

$$
\eta\,\mathbb E_i\|g_i\|^4\le2\mathbb E_i\|g_i\|^2.
$$

再用 $\mathbb E\|g_i\|^4\ge(\mathbb E\|g_i\|^2)^2$ 和 $\operatorname{tr}H=\mathbb E\|g_i\|^2$，就得到结论。

若改用较弱的损失稳定性，在低损失、光滑性与对齐条件下可以得到前述 Frobenius 范数控制。故“迹上界”和“Frobenius 上界”对应不同稳定性要求，不能直接互相替换。

先看稳定性如何约束对角线性网络表示的函数。

考虑

$$
f_\theta(x)=(a\odot b)^\top x=\beta^\top x,
\qquad \beta_j=a_jb_j.
$$

虽然预测函数是线性的，但参数化是非线性的。令 $\alpha_j=a_j^2+b_j^2$。对标准化输入分布，人口版本的 $G$ 的非零特征值恰好是 $\alpha_j$，所以

$$
\|G\|_2=\|\alpha\|_\infty,
\quad \|G\|_F=\|\alpha\|_2,
\quad \operatorname{tr}G=\|\alpha\|_1.
$$

有限样本下有相应概率界 [4]；这里先用人口版本的精确等式解释机制。

由于 $a_j^2+b_j^2\ge2|a_jb_j|$，

$$
\operatorname{tr}G\ge2\|\beta\|_1.
$$

于是稳定性可以控制最终预测函数的 $\ell_1$ 范数，而不只是控制冗余参数的一个任意量。

**定理 5.3** [4]。对特定的有界均匀输入分布和可实现线性目标 $f^*(x)=\beta^{*\top}x$，当 $n\gtrsim\log(d/\delta)$ 时，以至少 $1-\delta$ 的概率，任何符合上述 SGD 线性稳定性的插值解都满足

$$
\|\widehat\beta\|_1\lesssim\eta^{-1},
$$

$$
\boxed{
R(\widehat\theta)\lesssim
\frac{\eta^{-2}\log^2n\log d}{n}
+\frac{(\|\beta^*\|_1+\eta^{-1})^2\log(1/\delta)}{n}.
}
$$

这里 $R$ 是总体平方误差风险，$\lesssim$ 隐去固定常数。

这说明稳定性可以产生类似范数正则化的容量控制。它**没有**证明 SGD 精确求解了最小 $\ell_1$ 范数问题，也不等于证明 SGD 与 Lasso 是同一算法。

同样的思路也可以用于两层 ReLU 网络。

考虑两层网络

$$
f_\theta(x)=\sum_{j=1}^m a_j\operatorname{ReLU}(w_j^\top x),
\qquad
P(\theta)=\sum_j|a_j|\|w_j\|.
$$

$P$ 称为路径范数。对特定球面输入分布，可以建立曲率指标与加权参数平方和的联系 [4]；其中 Hessian 迹对应

$$
\sum_j(\|w_j\|^2+d a_j^2).
$$

而

$$
\sum_j(\|w_j\|^2+d a_j^2)\ge2\sqrt d\,P(\theta).
$$

因此，SGD 的迹约束能推出 $P(\widehat\theta_{\mathrm{sgd}})\lesssim1/(\eta\sqrt d)$；GD 的谱约束在这套分析中只给出 $P(\widehat\theta_{\mathrm{gd}})\lesssim1/\eta$。

**定理 4.3** [4]，省略对数因子的版本。对有界可实现目标、上述球面输入分布，以及满足样本量条件的情形，在同一学习率 $\eta$ 下，线性稳定插值解满足

$$
\boxed{
R(\widehat\theta_{\mathrm{sgd}})
\lesssim\widetilde O\left(\frac1{\eta^2n}\right),
\qquad
R(\widehat\theta_{\mathrm{gd}})
\lesssim\widetilde O\left(\frac d{\eta^2n}\right).
}
$$

它们是不显含网络宽度 $m$ 的界。完整结果的样本量前提仍依赖输入维数，约为 $d^2$ 量级再乘对数因子。因此，“与宽度无关”不等于“无维度要求、无数据要求”。

学习率有隐式正则化强度的作用。在该理论覆盖的模型中，更严格的稳定性约束能转化为更小的函数范数，而不是只得到一句笼统的“更平坦”。

考察隐式偏置时，初始化与稳定性要分开。小初始化本身也会带来偏置。使用较大初始化进行对照可以帮助辨认由稳定性产生的效果；这不意味着任意初始化都一定成功收敛。

选择与模型相匹配的复杂度指标。对角网络看有效系数 $\beta$ 的范数，两层 ReLU 看路径范数，比单独比较训练 loss 更能对应这里的理论。

不能据此宣布 SGD 总比 GD 泛化好。上面的比较固定同一学习率；改变学习率比例会改变界的比较。更重要的是，这些是特定模型与分布中的保证，尚非任意 Transformer、AdamW 或交叉熵训练的定理。

## 逃离不稳定区域时的运动方向

为了进一步区分整体与各个方向上的对齐，先考虑**未中心化的梯度二阶矩** $M$，定义

$$
\mu_M(\theta)=\frac{\operatorname{tr}(MG)}{2L\|G\|_F^2},
\qquad
g_M(\theta;v)=\frac{v^\top Mv}{2L\,v^\top Gv}.
$$

二者分别回答：噪声相关二阶矩对整体损失注入是否足够强，以及在某个方向上是否与该方向曲率同阶。只有分母非零时才直接使用这些比值。

若 $Gu_i=\lambda_i u_i$，则有一个简单而有用的恒等式：

$$
\mu_M=\sum_i\frac{\lambda_i^2}{\sum_j\lambda_j^2}\,g_M(\theta;u_i).
$$

整体对齐是按曲率平方加权的方向对齐平均。整体指标很好，并不保证每个方向都一样好。

在若干模型中，可以证明有限样本下的对齐性质 [5]。下表保留结论量级与重要条件，省略置信参数和对数因子的完整表达。

| 结果 | 模型与主要条件 | 结论的结构 |
|---|---|---|
| 定理 3.2、4.2 | $f_\theta(x)=F(\theta)^\top x$，高斯输入；样本量约为 $\widetilde O(d^2)$ | 对参数与方向统一控制对齐强度，条件不随参数维数 $p$ 增长 |
| 定理 3.3 | 普通线性模型；输入协方差有足够大的有效维数 | 在更低样本量区间仍可控制整体损失对齐 |
| 定理 3.5 | 固定输出权重的两层网络、高斯输入；$ 0\le\alpha\le\phi'\le\beta$ | 整体损失对齐有与网络宽度无关的上下界，常数依赖 $\alpha,\beta$ |
| 定理 4.3 | 普通线性模型、预先固定的有限组方向 | 方向对齐所需样本量可降至约 $\widetilde O(d)$ |

这里的非退化导数条件适合具有正斜率下界的 Leaky ReLU，不直接覆盖普通 ReLU 的全参数空间。预先固定的方向，也不能不加处理地替换为用同一训练数据估计出来的 Hessian 特征方向。

这些结果的重要性是：过参数化到很大的 $p$，不必让对齐保证随之失效。它们没有证明所有数据分布、所有网络、所有方向都严格满足同一个噪声公式。

一个高斯线性模型可以看清二阶矩与协方差的区别。

设 $x\sim N(0,I_d)$，$y=w_*^\top x$，当前误差向量为 $e=w-w_*$。有

$$
L=\tfrac12\|e\|^2,\qquad G=I,\qquad b=e.
$$

由高斯四阶矩公式，

$$
M=\mathbb E[(e^\top x)^2xx^\top]
=\|e\|^2I+2ee^\top,
$$

$$
\Sigma=M-bb^\top=\|e\|^2I+ee^\top.
$$

因此，若 $\varphi$ 是 $e$ 与 $v$ 的夹角，

$$
g_M(v)=1+2\cos^2\varphi\in[1,3],
\qquad
g_\Sigma(v)=1+\cos^2\varphi\in[1,2].
$$

这个例子说明，中心化会改变方向对齐的常数。讨论实际 SGD 方差时，必须从二阶矩中减去平均梯度的贡献，即使用 $\Sigma=M-bb^\top$。

接下来考察这些方向上的噪声如何影响逃离过程。

在插值解附近线性化，令 $G=H(\theta^*)$，$\mathcal L(\delta)=\delta^\top G\delta/2$。这一部分另外明确假设**真实噪声**满足

$$
A_1\mathcal L(\delta)\lambda_i
\le\mathbb E[(u_i^\top\xi)^2\mid\delta]
\le A_2\mathcal L(\delta)\lambda_i.
$$

常数中可以吸收固定 batch 的影响。此处不能仅凭对 $M$ 的结论就跳过中心化项。

定义前 $k$ 个较尖方向与剩余较平方向的损失能量

$$
X_t=\sum_{i\le k}\lambda_i\mathbb E[(u_i^\top\delta_t)^2],
\qquad
Y_t=\sum_{i>k}\lambda_i\mathbb E[(u_i^\top\delta_t)^2].
$$

**定理 5.2** [5]，保留核心量级的版本。在上述方向对齐假设下，取 $\eta=\beta/\|G\|_F$，且常数 $\beta$ 足够大。对非零初始损失，线性化 SGD 处于逃离的不稳定区间；经过定理给定的短暂过渡后，

$$
\boxed{
\frac{Y_t}{X_t}\gtrsim
\frac{\sum_{i>k}\lambda_i^2}{\sum_{i\le k}\lambda_i^2}.
}
$$

特别地，取 $k=1$，较平方向与最陡方向的能量比受 $\sum_i\lambda_i^2/\lambda_1^2-1$ 控制。这个有效谱维数很大时，最陡的一个方向不再占据全部运动。

与之比较，**命题 5.3** [5] 表明：GD 若在 $\eta\lambda_1>2$ 的不稳定区间，且 $\lambda_1>\lambda_2$、初始扰动在 $u_1$ 上非零，那么它的逃离会渐渐由最陡方向主导。

这个结论与噪声在单个陡峭方向上更强并不矛盾。

设 $\lambda_1=10$，另外有 1000 个特征值都为 1。最陡方向的单方向噪声更强，但曲率平方总量分别为

$$
\lambda_1^2=100,\qquad \sum_{i>1}\lambda_i^2=1000.
$$

大量中低曲率方向合起来，可以比一个最陡方向承载更多能量。这里的“平缓方向”是相对于顶部特征方向而言，**不特指曲率严格为零的零空间**；在上述假设下，$\lambda_i=0$ 的方向也没有该项噪声注入。

只检查第一特征向量可能误判运动。可以把参数位移投影到若干谱区间，比较顶部方向与剩余方向的聚合贡献。

循环学习率具有几何上的探索解释。提高学习率能使当前区域失稳，SGD 的多方向运动可能帮助沿低损失谷移动，再降低学习率重新稳定。这一解释有相应模型和实验支持 [5]；这不是对任意训练任务的性能保证。

不要把一次 spike 直接解释为成功逃离坏极小值。需要同时观察后续曲率、验证集表现与运动方向，才能区分有效探索和单纯训练失稳。

## 等价参数化与噪声平衡

最简单的例子是 $f_{u,v}(x)=uvx$。对任意 $c>0$，

$$
(u,v)\longmapsto(cu,v/c)
$$

不改变预测函数，也不改变每个样本的损失。但 $u,v$ 的范数、梯度尺度和参数空间 Hessian 可以改变。

因此，除了“在不同函数之间选择”，优化器还可能**在表示同一函数的不同参数化之间选择**。

先比较梯度流与有限步长更新对这种尺度差异的影响。

设单样本损失依赖于乘积 $uv$，记 $q=\partial\ell/\partial(uv)$。梯度流满足

$$
\dot u=-qv,\qquad \dot v=-qu,
$$

所以

$$
\frac d{dt}(u^2-v^2)=0.
$$

若初始化时两层尺度不平衡，这个差值在理想梯度流下不会消失。

但一次有限步长更新满足

$$
u'=u-\eta qv,\qquad v'=v-\eta qu,
$$

直接展开得到

$$
\boxed{u'^2-v'^2=(1-\eta^2q^2)(u^2-v^2).}
$$

在合适步长、且 $q$ 持续非零时，这个更新倾向于缩小不平衡。若 $q$ 是随机量，$\mathbb E q^2=(\mathbb E q)^2+\operatorname{Var}(q)$，随机性会额外影响收缩强度。

这个例子也提醒我们：**严格守恒的是梯度流；有限步长的 GD 也可能打破守恒。** 不能简化成“只有 SGD 会重平衡，GD 永远不会”。

为了更一般地描述这种机制，考虑对称矩阵 $A$ 生成的指数对称性：

$$
\ell_i(e^{\lambda A}\theta)=\ell_i(\theta),\qquad \forall i,\lambda.
$$

令 $Q(\theta)=\theta^\top A\theta/2$。它是梯度流对应的守恒量，称为 Noether 量。这里的 $A$ 要满足相应对称条件，并非任意连续对称都直接套用同一个二次公式。

为了明确常数，本文采用如下 SDE 与权重衰减约定：

$$
d\theta=-(\nabla L+2\gamma\theta)\,dt
+\sqrt{2\tau}\,\Sigma(\theta)^{1/2}dW,
\qquad \tau=\frac\eta{2B}.
$$

因为每个样本梯度都与 $A\theta$ 正交，Itô 公式给出

$$
\boxed{\dot Q=-4\gamma Q+\tau\operatorname{tr}(A\Sigma).}
$$

这里的 $\dot Q$ 表示 $Q$ 的条件漂移，而不是含噪声轨迹逐点的普通导数；这个漂移称为 Noether flow。没有权重衰减时，其平衡条件是 $\operatorname{tr}(A\Sigma)=0$。

**定理 4.3** [6]，保留关键条件的转述。对固定对称轨道 $\theta_\lambda=e^{\lambda A}\theta$，上述漂移作为 $\lambda$ 的函数单调不增，并存在平衡位置；位置允许在 $\lambda=\pm\infty$。在漂移不退化的条件下，平衡位置唯一；若协方差足够光滑，有限平衡位置还具有相应光滑性。

它为何有单调性？因为

$$
\Sigma(\theta_\lambda)=e^{-\lambda A}\Sigma(\theta)e^{-\lambda A},
\qquad
\frac d{d\lambda}\operatorname{tr}(A\Sigma(\theta_\lambda))
=-2\operatorname{tr}(A^2\Sigma(\theta_\lambda))\le0,
$$

同时 $dQ(\theta_\lambda)/d\lambda=\theta_\lambda^\top A^2\theta_\lambda\ge0$。因此，当存在非退化有限根时，两侧的漂移具有恢复平衡的方向。

必须准确理解“唯一”：它是给定轨道及相关条件下的平衡，不是整个网络唯一的最优参数，也不是证明最后学到的函数与初始化无关。真实训练中平衡位置本身还可能移动；在额外条件下也可以分析对移动平衡的跟踪 [6]。

此外，Noether 量发生变化不意味着每次梯度噪声都直接沿对称切向推参数；逐样本梯度恰好与该切向正交。系统性变化可以来自有限步长或 Itô 二阶项。

在两层线性网络中，平衡条件可以写得更具体。

考虑 $f(x)=UWx$。其参数对称性为 $U\mapsto UR$、$W\mapsto R^{-1}W$。

**定理 5.2** [6] 的一个特例是：假设目标满足 $y=V_*x+\epsilon$，输入和零均值标签噪声独立，在实现最优映射 $UW=V_*$ 时，不加权重衰减。记输入与输出噪声协方差为 $\Sigma_x,\Sigma_\epsilon$，且噪声非退化，则噪声平衡条件化为

$$
\boxed{
W\overline\Sigma_xW^\top
=U^\top\overline\Sigma_\epsilon U,
\qquad
\overline\Sigma=\frac\Sigma{\operatorname{tr}\Sigma}.
}
$$

左侧描述输入经过第一层后的结构，右侧描述输出噪声反传到隐藏层的结构。平衡的是这些数据加权的矩阵，而不只是两个权重的欧氏范数。

如果输入与输出噪声都各向同性，条件进一步变成

$$
\frac{WW^\top}{d_x}=\frac{U^\top U}{d_y}.
$$

只有在特定维数与尺度设置下，才能再简化成两个 Gram 矩阵相等。

**定理 5.4** [6] 将这种分析推广到深线性网络，并构造一类噪声平衡解：在有效秩对应的子空间中，中间层具有相同尺度的非零奇异值；两端层还需结合输入和输出噪声协方差进行加权。隐藏空间中的正交自由度仍然保留，因此它不是“所有层矩阵唯一”或“所有层原始范数都相等”的结论。

平衡参数尺度时，局部曲率也会随之变化。

噪声平衡的目标条件是 $\dot Q=0$，并不等于最小化 $\operatorname{tr}H$。对于上述两层线性模型，平方损失的 Hessian 迹为

$$
\operatorname{tr}H
=d_y\|W\Sigma_x^{1/2}\|_F^2
+\operatorname{tr}(\Sigma_x)\|U\|_F^2.
$$

沿着等价参数化调整 $U,W$，这个量可能增加，也可能降低。数据分布、噪声方向和初始不平衡都会影响变化方向。

这与稳定性筛选并不矛盾：稳定性约束“某处是否容许驻留”，噪声平衡描述“某些等价参数化之间的系统性漂移”。二者没有声称同一个量必须全程单调下降。

层间尺度是训练状态的一部分。只看总 loss，可能看不到层范数、激活协方差和梯度噪声结构仍在变化。

归一化与层间平衡有动力学意义。它们可能改变等价参数化中的位置和局部条件数。因此可以从这一角度考察归一化的影响，但不能认为所有归一化都等价于最小化 Hessian 迹。

Warmup 可以用“先改善局部可训练性”理解。较小步长允许早期尺度调整，之后再提高步长；但噪声平衡也可能导致变尖，因此这只是解释和实验线索，这不能直接给出通用的 warmup 步数公式。

比较 sharpness 前要固定参数化与尺度约定。同一个预测函数，仅仅重缩放参数，就可能改变原始 Hessian。

平衡机制需要驱动力。在精确插值、所有单样本梯度都为零且无衰减时，噪声项也为零，不能声称系统还会继续消除一切初始化差异。

## 自适应优化器的动力学

前面的讨论主要围绕 SGD。换成自适应优化器，还要考虑一个现象：**训练中的振荡或 loss spike，不一定来自小 batch 噪声；即使使用全梯度，Adam 也可能出现这些现象。**

沿用常见记号，Adam 为

$$
m_{t+1}=\beta_1m_t+(1-\beta_1)g_t,
\qquad
v_{t+1}=\beta_2v_t+(1-\beta_2)g_t^{\odot2},
$$

$$
\theta_{t+1}=\theta_t-\eta
\frac{\widehat m_{t+1}}{\sqrt{\widehat v_{t+1}}+\varepsilon}.
$$

帽号表示偏差修正，运算按坐标进行。下面的分析主要考虑全 batch、固定学习率；相关实验采用平方损失，也包括分类任务。大 batch 随机 Adam 有部分实验支持，小 batch 情况仍需另外分析。

分析重点是连续极限与定点附近的离散行为，不能由此断定 Adam 必然比 SGD 泛化更好。

**命题 1** [7]。假设目标梯度有界且 Lipschitz 连续，固定 $\beta_1,\beta_2\in(0,1)$ 和 $\varepsilon>0$，令 $\eta\to0$，并使用连续时间 $t=k\eta$。在任意固定有限时间区间，Adam/RMSprop 的参数轨迹收敛到

$$
\boxed{\dot\theta=-\frac{\nabla L(\theta)}{|\nabla L(\theta)|+\varepsilon}.}
$$

在梯度坐标相对 $\varepsilon$ 不小的区域，它近似

$$
\dot\theta=-\operatorname{sign}(\nabla L(\theta)).
$$

直觉是：固定动量系数意味着记忆跨越大致固定数量的更新步；当每一步代表的连续时间趋零，记忆对应的连续时间长度也趋零，于是 $m$ 和 $v$ 快速跟踪当前梯度及其平方。

这里必须保留 $\varepsilon$：固定 $\varepsilon>0$ 时，严格极限是上面的平滑化表达，不是处处等于 signGD，更不能直接从这个命题推出离散 Adam 有限步精确收敛。

若改为

$$
\beta_1=1-b\eta,\qquad \beta_2=1-a\eta,
\qquad a,b>0,
$$

动量记忆在连续时间中不会消失。

**命题 2** [7]。在相应光滑性条件、零初始动量等设置下，轨迹收敛到保留状态变量的 ODE：

$$
\dot m=b(\nabla L-m),\qquad
\dot v=a((\nabla L)^{\odot2}-v),
$$

$$
\dot\theta=-\frac{m/(1-e^{-bt})}
{\sqrt{v/(1-e^{-at})}+\varepsilon}.
$$

**命题 3** [7] 又说明，在初始各坐标梯度远离零、$\varepsilon=0$ 等额外条件下，即便使用保留记忆的 ODE，其最初短时间的速度仍接近 signGD，偏差可用随时间线性增长的上界控制。

这里最实用的认识是：**“Adam 的连续极限”不是唯一一个公式，取决于学习率与动量参数如何一起缩放。**

假设目标满足 Polyak–Łojasiewicz 条件

$$
\|\nabla L(\theta)\|_2^2\ge
\mu_{\mathrm{PL}}(L(\theta)-L_*),\qquad \mu_{\mathrm{PL}}>0.
$$

它要求：只要损失仍高于最优值，梯度就不能过小。PL 条件不要求目标一定是强凸函数。

**命题 4** [7]。对理想 signGD 流，令 $h(t)=L(\theta(t))-L_*$，则到达最优值之前

$$
\boxed{
h(t)\le\left(\sqrt{h(0)}-\frac{\sqrt{\mu_{\mathrm{PL}}}}2t\right)^2,
\qquad
T_*\le2\sqrt{\frac{h(0)}{\mu_{\mathrm{PL}}}}.
}
$$

到达后保持在最优值；若写覆盖所有时间的表达，可将括号替换为其正部。

这个证明很短：

$$
\dot h=-\|\nabla L\|_1
\le-\|\nabla L\|_2
\le-\sqrt{\mu_{\mathrm{PL}}h},
\qquad
\frac d{dt}\sqrt h\le-\frac{\sqrt{\mu_{\mathrm{PL}}}}2.
$$

它为早期快速下降提供了一个解释，但连续时间有限时间到达，不等于离散算法有限次更新精确到达；两种算法的“时间单位”与每步位移也不相同。

连续流的收敛并不意味着离散更新不会振荡。

考虑全 batch RMSprop 在驻点附近的情形。若梯度衰减使 $v$ 接近零，则

$$
\theta_{t+1}\approx\theta_t-\frac\eta\varepsilon\nabla L(\theta_t).
$$

相当于有效步长被放大到 $\eta/\varepsilon$。无一阶动量时，局部二次模型的稳定性要求近似为

$$
\eta\lambda_{\max}(H)\lesssim2\varepsilon.
$$

当 $\varepsilon$ 很小、学习率固定时，这个要求非常苛刻。Adam 加入一阶动量后，精确边界还会依赖动量参数，不能直接照搬这个 RMSprop 阈值。

一个可直接验证的例子是 $L(x)=x^2/2$，取 $\varepsilon=0$。RMSprop 存在二周期轨道

$$
x_t\in\left\{\frac\eta2,-\frac\eta2\right\},
\qquad v_t=\frac{\eta^2}{4}.
$$

因为两点处的梯度平方相同，$v$ 保持不变；每次更新的位移大小为 $\eta$，刚好在两点间来回跳。损失为 $\eta^2/8$，不会继续下降到零。该例说明二周期的存在，不意味着所有高维任务都收敛到同一类二周期。

除了有效步长，一阶和二阶动量的时间尺度也会影响振荡。

沿用上面的记号，$a=(1-\beta_2)/\eta$、$b=(1-\beta_1)/\eta$。实验中观察到三类区域 [7]：

| 时间尺度关系 | 实验中的典型行为 |
|---|---|
| $b$ 显著大于 $a$ | 可能反复出现较大 spike |
| $a$ 与 $b$ 接近 | 通常为幅度较小、较快的振荡，训练较平稳 |
| $a$ 显著大于 $b$ | 可能进入发散区域 |

例如 $\beta_1=0.9,\beta_2=0.999$ 对应 $b/a=100$。一阶、二阶统计的响应速度相差很大。在所测任务中，使两者时间尺度更接近，可以减轻后期 spike，特别有利于追求低训练误差的函数拟合与 PDE 求解。

这只是所测任务中的定性实验规律，不能当作任意目标函数上的完整稳定性分区。

排查 spike 时，先确定它是否需要抽样噪声。在固定数据、关闭额外随机源的全 batch 或大 batch 对照中仍复现的 spike，可能主要来自优化器内部动力学。

观察真正的更新量，而不只看原始梯度。记录 $\eta\widehat m/(\sqrt{\widehat v}+\varepsilon)$、其相对参数范数，以及分母的分布，往往比只看 $\|g\|$ 更有解释力。

高精度回归和科学计算中，应联合调节学习率、动量时间尺度与 $\varepsilon$。后期降低学习率、检查两个动量统计的响应差异，都是由本文机制支持的实验方向；增大 $\varepsilon$ 也会改变有效预条件，而不是一个完全中性的数值修补。

不要直接把“$\beta_1\approx\beta_2$ 更好”当成通用 LLM 配方。上述实验主要研究固定学习率、全 batch、平方损失，不能证明这一选择适用于所有小 batch、交叉熵、AdamW 或大模型任务。

## 训练中的曲率与噪声测量

为了比较自适应方法中的曲率，先忽略动量变化，把某一时刻的正定对角预条件矩阵 $P$ 暂时冻结。预条件 GD 的局部更新为

$$
\delta_{t+1}=(I-\eta PH)\delta_t.
$$

由于 $PH$ 与 $P^{1/2}HP^{1/2}$ 相似，局部稳定性由

$$
\eta\lambda_{\max}(P^{1/2}HP^{1/2})
$$

控制，而不是只看未经预条件的 $\eta\lambda_{\max}(H)$。随机更新的噪声协方差也变成 $P\Sigma P$。

这是一个帮助迁移直觉的短推导，不是完整 Adam 定理：真实 Adam 的 $P_t$ 在变化，还与梯度、动量相互耦合。其价值在于说明，比较 SGD 和 Adam 时，单独报告原始 Hessian 指标可能不够。

对大模型，显式存储 $p\times p$ 矩阵不可行。但可以在固定 checkpoint 上，通过 Hessian–vector product，简称 HVP，估计部分量。

若随机向量 $z$ 满足 $\mathbb E[zz^\top]=I$，则

$$
\mathbb E[z^\top Hz]=\operatorname{tr}H,
\qquad
\mathbb E\|Hz\|^2=\|H\|_F^2.
$$

因此，少量随机探针可以提供迹与 Frobenius 范数平方的估计；最大特征值可以用基于 HVP 的特征值迭代估计。实际精度取决于探针数量、谱形状和数值误差。

估计噪声时，应先固定参数，独立采集 $K$ 个大小为 $B$ 的 batch 梯度 $\widehat g^{(k)}$，令其平均为 $\overline g$。在独立有放回抽样模型下，单样本协方差的无偏估计为

$$
\widehat\Sigma=
\frac B{K-1}\sum_{k=1}^K
(\widehat g^{(k)}-\overline g)(\widehat g^{(k)}-\overline g)^\top.
$$

不需要显式形成这个矩阵。令 $d_k=\widehat g^{(k)}-\overline g$，直接计算

$$
\widehat{\operatorname{tr}(H\Sigma)}
=\frac B{K-1}\sum_k d_k^\top H d_k.
$$

这需要额外梯度与 HVP，适合定期诊断，不必每步计算。若参数在采样过程中变化，测到的差异就同时混入了轨迹变化，不能再直接解释成固定位置的梯度噪声。

还应留意：远离极小值时 $H$ 可能不定，迹会发生正负抵消，$\operatorname{tr}(H\Sigma)$ 也未必为正。前文很多“总曲率”“噪声注入损失”的直觉，明确建立在局部正半定区域；需要正半定曲率代理时，应区分 $G$ 与真实 $H$。

训练现象往往有多种可能的成因。比较曲率、噪声方向、参数尺度和实际更新量，并结合适当的对照实验，才能判断哪种机制与观察更吻合。

## 参考文献与证明索引

**[1]** Lei Wu, Chao Ma, Weinan E. *How SGD Selects the Global Minima in Over-parameterized Learning: A Dynamical Stability Perspective.* NeurIPS 2018.

- [论文页面](https://proceedings.neurips.cc/paper_files/paper/2018/hash/6651526b6fb8f29a00507de6a49ce30f-Abstract.html)
- [PDF](https://proceedings.neurips.cc/paper_files/paper/2018/file/6651526b6fb8f29a00507de6a49ce30f-Paper.pdf)
- 重点：§3.1、定理 1；证明见附录 A。注意矩阵条件在一般高维为充分条件，一维为充要条件。

**[2]** Zhanxing Zhu, Jingfeng Wu, Bing Yu, Lei Wu, Jinwen Ma. *The Anisotropic Noise in Stochastic Gradient Descent: Its Behavior of Escaping from Sharp Minima and Regularization Effects.* ICML 2019, PMLR 97:7654–7663.

- [论文页面及补充材料入口](https://proceedings.mlr.press/v97/zhu19e.html)
- [arXiv:1803.00195](https://arxiv.org/abs/1803.00195)
- 重点：§3 的局部逃离指标、式 (13)、命题 1；§4 的命题 2、3。长证明见补充材料，命题证明在 A.3—A.5。

**[3]** Lei Wu, Mingze Wang, Weijie Su. *The alignment property of SGD noise and how it helps select flat minima: A stability analysis.* NeurIPS 2022.

- [arXiv:2207.02628](https://arxiv.org/abs/2207.02628)
- [本文所用 v3 PDF](https://arxiv.org/pdf/2207.02628v3)
- 重点：§2 的对齐性质，§3 的定义 3.1、定理 3.3、3.5。本文把其稳定性称为“损失稳定性”，以便与 [4] 区分。

**[4]** Lei Wu, Weijie J. Su. *The Implicit Regularization of Dynamical Stability in Stochastic Gradient Descent.* ICML 2023.

- [arXiv:2305.17490](https://arxiv.org/abs/2305.17490)
- [PDF](https://arxiv.org/pdf/2305.17490)
- 重点：命题 3.2 与附录 B.1；ReLU 网络定理 4.1、4.3 与附录 C；对角线性网络定理 5.2、5.3 与附录 D。理论中的 SGD batch size 为 1。

**[5]** Mingze Wang, Lei Wu. *A Theoretical Analysis of Noise Geometry in Stochastic Gradient Descent.* arXiv:2310.00692，初稿 2023；本文采用 2024 年 2 月 1 日的 v3。

- [论文页面](https://arxiv.org/abs/2310.00692)
- [v3 PDF](https://arxiv.org/pdf/2310.00692v3)
- 重点：定理 3.2、3.3、3.5，定理 4.2、4.3，以及定理 5.2、命题 5.3；对应长证明在附录 B、C、D。按 v3 的未中心化二阶矩定义，高斯线性模型中方向对齐可达 3；定理 4.2、4.3 的相应上界趋于 2，需注意其与中心化协方差的常数区别。

**[6]** Liu Ziyin, Mingze Wang, Hongchao Li, Lei Wu. *Parameter Symmetry and Noise Equilibrium of Stochastic Gradient Descent.* NeurIPS 2024.

- [arXiv:2402.07193](https://arxiv.org/abs/2402.07193)
- [本文所用 v3 PDF](https://arxiv.org/pdf/2402.07193v3)
- 重点：定理 4.3、4.5 与附录 B；定理 5.2 与附录 C；Remark 4.4、附录 D 对有限步长的讨论；定理 5.4 与附录 E。本文重新固定了二次 Noether 量及 SDE 系数的归一化，使用时应以本文给出的约定为准。

**[7]** Chao Ma, Lei Wu, Weinan E. *A Qualitative Study of the Dynamic Behavior for Adaptive Gradient Algorithms.* Proceedings of the 2nd Mathematical and Scientific Machine Learning Conference, PMLR 145:671–692, 2022。会议于 2021 年举行；arXiv 初稿发表于 2020 年。

- [论文集页面](https://proceedings.mlr.press/v145/ma22a.html)
- [arXiv:2009.06125](https://arxiv.org/abs/2009.06125)
- [本文所用 arXiv v2 PDF](https://arxiv.org/pdf/2009.06125v2)
- 重点：命题 1—3 与 §2.2、附录 A、B；命题 4 与 §3；spike/oscillation/divergence 的定性实验见 §4。动量分区属于实验结论，不应标注为普适定理。

```

```
