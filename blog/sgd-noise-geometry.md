

# 优化器究竟在选择什么？

神经网络训练并不只有“把训练损失降下来”这一个问题。过参数化模型往往有很多训练误差相同的解，但不同优化器、学习率、batch size 和初始化，最后会得到不同的参数，甚至不同的测试性能。

本文围绕一个问题展开：**当训练误差已经很低时，更新规则还在筛选什么、推动什么？**

从随机梯度的基本性质出发，我们将依次讨论稳定性、噪声方向、函数复杂度和参数尺度，最后看看自适应优化器带来的新现象。

## 预备知识

先把训练停在某一个参数 $\theta$ 上，想象从同一个数据集反复抽 batch。每次拿到的梯度都不一样，我们希望先算清楚两件事。抽样的平均方向是什么，单次抽样又会偏离它多少？

记训练集大小为 $n$，参数维数为 $p$，输入维数为 $d$。训练目标是单样本损失的平均。

$$
L(\theta)=\frac1n\sum_{i=1}^n\ell_i(\theta).
$$

写 $s_i(\theta)=\nabla\ell_i(\theta)$，从所有样本中等概率抽一个时，梯度的平均就是 $b(\theta)=\nabla L(\theta)$。若直接把 $s_i s_i^\top$ 平均，得到了包含平均方向在内的二阶矩。要量围绕 $b$ 的波动，就把 $s_i$ 换成 $s_i-b$ 再算一次。

$$
M(\theta)=\frac1n\sum_i s_i s_i^\top,
\qquad
\Sigma(\theta)=M(\theta)-b(\theta)b(\theta)^\top.
$$

展开后正好扣掉 $bb^\top$。这一步值得留意，后文有些计算从 $M$ 出发，真正进入 SGD 抽样误差的是 $\Sigma$。

若 batch 里 $B$ 次抽样独立且有放回，平均梯度的误差是 $B$ 个零均值项相加后除以 $B$。方差先加 $B$ 次，再除以 $B^2$，因此

$$
\widehat g_B=b+\xi_B,
\qquad \mathbb E[\xi_B\mid\theta]=0,
\qquad \operatorname{Cov}(\xi_B\mid\theta)=\frac{\Sigma(\theta)}B,
$$

把这个分解写进一次更新，便能同时看到平均下降与抽样波动。

$$
\theta_{t+1}=\theta_t-\eta\bigl(b(\theta_t)+\xi_{B,t}\bigr).
$$

若从有限数据集中无放回抽 $B$ 个样本，抽样误差之间不再独立，$\Sigma$ 前的因子变为

$$
\frac{n-B}{B(n-1)}.
$$

把 $B$ 取到 $n$，这个因子就为零。两种抽样模型都说明，在参数位置固定时，增大 batch 会减小抽样误差。这里把每个 $\ell_i$ 视为固定的单样本损失。Dropout、随机数据增强或依赖整个 batch 的计算需要另外计入。接下来要问的是，参数挪一点以后，噪声会不会也跟着变？

平方损失给了一个可以直接看清这件事的例子。令标量输出为 $f_\theta(x_i)$，取

$$
\ell_i(\theta)=\frac12\bigl(f_\theta(x_i)-y_i\bigr)^2.
$$

记残差 $r_i=f_\theta(x_i)-y_i$、输出梯度 $g_i=\nabla_\theta f_\theta(x_i)$。对损失求一次导数，得到单样本梯度 $s_i$。把 $g_i g_i^\top$ 平均，得到平方损失的 Gauss–Newton 矩阵 $G$。

$$
s_i=r_i g_i,
\qquad
G(\theta)=\frac1n\sum_i g_i g_i^\top,
$$

再求一次导数会有两项，一项来自对残差求导，另一项来自对输出梯度求导。

$$
H(\theta)=\nabla^2L(\theta)
=G(\theta)+\frac1n\sum_i r_i\nabla^2 f_\theta(x_i).
$$

因此 $G$ 可以在残差为零时保留曲率，而梯度二阶矩 $M$ 还带着残差的平方。在插值解 $\theta^*$ 处，所有 $r_i=0$，于是

$$
H(\theta^*)=G(\theta^*),\qquad
s_i(\theta^*)=0,\qquad \Sigma(\theta^*)=0.
$$

恰好站在这里，没有额外随机源，抽到哪个样本都给零梯度。讨论这个点稳不稳定，要从一个很小的扰动出发，看看残差、梯度和噪声会怎样重新出现。

如果扰动朝不同方向，曲率的影响也会不同。比如 $H_1=\operatorname{diag}(10,0,\ldots,0)$ 与 $H_2=10I_{100}$，最陡方向的曲率都是 $10$。后者却有一百个这样的方向，所以 Frobenius 范数分别为 $10$ 与 $100$，迹分别为 $10$ 与 $1000$。在局部 $H\succeq0$、特征值为 $\lambda_1\ge\cdots\ge\lambda_p\ge0$ 时，三个数各自概括了不同的谱信息。

| 指标 | 公式 | 直观含义 |
|---|---|---|
| 最大特征值 | $\|\|H\|\|_2=\lambda_1$ | 最陡的那个方向 |
| Frobenius 范数 | $\|\|H\|\|_F=(\sum_i\lambda_i^2)^{1/2}$ | 各方向曲率的平方总量 |
| 迹 | $\operatorname{tr}H=\sum_i\lambda_i$ | 各方向曲率的总和 |

后文会看到，有的稳定性条件只需要最陡方向，有的需要把许多方向的贡献加起来。先用一维的 $L(x)=\lambda x^2/2$ 看最熟悉的那一种。连续梯度流 $\dot\theta=-\nabla L(\theta)$ 在这里给出 $x(t)=e^{-\lambda t}x(0)$。GD 的 $\theta_{t+1}=\theta_t-\eta\nabla L(\theta_t)$ 则走有限步。

$$
x_{t+1}=(1-\eta\lambda)x_t.
$$

只要 $|1-\eta\lambda|\le1$，扰动的绝对值就不会放大，即 $0\le\eta\lambda\le2$。端点可以维持扰动而不消失，严格收缩还需要 $|1-\eta\lambda|<1$。这样看，学习率也参与决定了哪些解在更新下可以稳定驻留。

如果这种筛选最后表现为对函数范数、局部曲率或层间尺度的偏好，就属于本文讨论的隐式正则化。显式正则化则把 $\lambda R(\theta)$ 直接加进目标。接下来的分析关心更新本身怎样产生这些偏好。这里把“动态稳定性”用于参数受到扰动后的演化，学习理论里替换一个样本后输出会变多少，属于算法稳定性问题。

## 稳定性与样本间的差异

先从两个平均损失完全一样的训练集开始。每个样本的损失为 $\ell_i(x)=a_ix^2/2$，每步抽一个。若平均曲率为 $a=\mathbb E a_i$，样本间的方差为 $s^2=\operatorname{Var}(a_i)$，把更新 $x_{t+1}=(1-\eta a_i)x_t$ 平方再取条件期望，有

$$
\mathbb E[x_{t+1}^2\mid x_t]
=\mathbb E[(1-\eta a_i)^2]x_t^2
=\bigl((1-\eta a)^2+\eta^2s^2\bigr)x_t^2.
$$

先猜一猜，如果两组的 $a$ 都是 $1$，学习率都取 $1.5$，扰动会怎样？把两种样本构成代进去。

| 样本曲率 | 平均曲率 $a$ | 非均匀性 $s$ | $\eta=1.5$ 时的二阶矩倍数 |
|---|---:|---:|---:|
| $(1,1)$ | 1 | 0 | 0.25 |
| $(0,2)$ | 1 | 1 | 2.5 |

两组的全梯度一样，GD 对它们给出相同的更新。SGD 的第二组却会因 $a_i$ 在 $0$ 与 $2$ 之间跳动，把二阶矩每步放大 $2.5$ 倍。平均曲率这一项在两组都给 $0.25$，造成差别的是随机曲率的方差。

把这个算式搬到多维。设 $\theta^*$ 处每个样本都达到极小值，取扰动 $\delta=\theta-\theta^*$，写出局部二次近似。

$$
\ell_i(\theta^*+\delta)\approx\frac12\delta^\top H_i\delta,
\qquad H=\frac1n\sum_i H_i.
$$

在全梯度里，每一步用平均 Hessian $H$。在 SGD 里，每步用 batch 抽到的样本 Hessian 的平均。要复现一维算式里的 $s^2$，可以把 $H_i-H$ 平方再平均，定义

$$
V=\frac1n\sum_iH_i^2-H^2
=\frac1n\sum_i(H_i-H)^2,
$$

记 $a=\lambda_{\max}(H)$、$s=\sqrt{\lambda_{\max}(V)}$。这里的 $V$ 衡量样本曲率相对平均曲率的波动。若每一步独立抽取 batch，batch 内无放回、大小为 $B$，给定 $\delta_t$ 后，把更新矩阵的平方取期望，交叉项因抽样曲率的均值为 $H$ 而消失，额外的平方项带上无放回抽样因子。若整个矩阵在任何方向上都不把二阶矩放大，也就是满足

$$
\boxed{
\lambda_{\max}\left((I-\eta H)^2+
\eta^2\frac{n-B}{B(n-1)}V\right)\le1,
}
$$

就能使线性化扰动满足 $\mathbb E\|\delta_t\|^2\le C\|\delta_0\|^2$，这里 $C$ 与 $t$ 无关。这是定理 1 按统一记号写出的充分条件。在一维里，上式直接给出每轮的二阶矩倍数，因此也是必要条件。 [1]

顺着两项分别看，$a\le2/\eta$ 和非均匀性的单独上界，是这个矩阵判据成立所需的约束。一般高维的稳定性还要看整个更新的作用。调 $\eta$ 会同时改变平均更新和随机放大，调 $B$ 主要改变抽样项，固定 $\eta/B$ 并不会固定上式。如果 GD 在一处稳定，而小 batch SGD 波动很大，可以检查样本梯度或曲率的差异。这个条件回答的是局部扰动能否留在附近，要从这种筛选谈到泛化，还缺少把曲率转成函数复杂度的一步。

## 噪声的方向与曲率

同样多的噪声，放到最陡和最平缓的方向，loss 会增加一样多吗？在局部二次损失里，沿特征向量 $u_i$ 偏移同样远，代价会乘上不同的曲率 $\lambda_i$。为了把这个观察写成一条式子，在小步长近似下用 SDE 表示 SGD。

$$
d\theta_t=-\nabla L(\theta_t)\,dt+S(\theta_t)^{1/2}dW_t.
$$

这里 $S$ 是扩散协方差。以 $t=k\eta$ 匹配时间时，常用 $S\approx\eta\Sigma/B$。应用 Itô 公式，噪声的均值为零，二阶项却会在期望里留下来。

$$
\boxed{
\frac{d}{dt}\mathbb E L(\theta_t)
=-\mathbb E\|\nabla L(\theta_t)\|^2
+\frac12\mathbb E\operatorname{tr}\bigl(H(\theta_t)S(\theta_t)\bigr).
}
$$

第一项是梯度流对损失的降低量。在 $H\succeq0$ 的局部区域，第二项是噪声带来的损失注入。把 $H=\sum_i\lambda_i u_iu_i^\top$ 代进去，马上能读出方差在各个方向的贡献。

$$
\operatorname{tr}(HS)=\sum_i\lambda_i\,u_i^\top S u_i.
$$

$u_i^\top S u_i$ 是投到第 $i$ 个方向的噪声方差，再乘该方向的曲率才知道它对 loss 有多大影响。只量 $\operatorname{tr}S$，相当于只把这些方差加起来，还没区分它们落在哪里。

还能把短时间的增量算得更具体。取 $L(\theta)-L(0)=\theta^\top H\theta/2$，令 $H\succ0$、$S$ 为常矩阵，从 $\theta_0=0$ 起步。此时得到 Ornstein–Uhlenbeck 过程，其期望损失可直接算成下式。 [2]

$$
\boxed{
\mathbb E[L(\theta_t)-L(0)]
=\frac14\operatorname{tr}\bigl[(I-e^{-2Ht})S\bigr]
=\frac t2\operatorname{tr}(HS)+O(t^2).
}
$$

展开 $e^{-2Ht}$，开头的斜率正好是 $\operatorname{tr}(HS)/2$。再往后，固定正定二次模型中的期望损失会饱和。因此这里用增长速度来比较局部“逃离效率”，真实非线性势阱的首次退出时间还需要势阱范围内的动力学。

若想与各向同性噪声作比较，可以先把总方差固定为同一个 $\operatorname{tr}S$，令 $\overline S=(\operatorname{tr}S/p)I$。在 $\operatorname{tr}H,\operatorname{tr}S$ 都为正时，假设最陡方向至少分到下面这么多方差。

$$
u_1^\top S u_1\ge a\lambda_1\frac{\operatorname{tr}S}{\operatorname{tr}H},\qquad a>0.
$$

只取 $\operatorname{tr}(HS)$ 里第一项，就足以给出注入量的比例下界。

$$
\frac{\operatorname{tr}(HS)}{\operatorname{tr}(H\overline S)}
=\frac{p\operatorname{tr}(HS)}{\operatorname{tr}H\operatorname{tr}S}
\ge a p\frac{\lambda_1^2}{(\operatorname{tr}H)^2}.
$$

曲率若集中在少数方向，$\lambda_1/\operatorname{tr}H$ 可以很大。取 $H=\operatorname{diag}(\lambda,0,\ldots,0)$，相同的总方差全部放在第一个方向，注入量正好是各向同性的 $p$ 倍。这是命题 1 所刻画的机制。固定输出层、分段线性激活和特定裁剪输出的单隐层模型里，命题 2、3 还能建立二阶矩、协方差与 Hessian 的关系，为对齐提供模型内的依据。 [2]

所以，用与 SGD 总方差相同的各向同性高斯噪声作对照，可以检验噪声方向的作用。要知道控制住总量后差异还在不在，可以看主特征方向上的投影或 $\operatorname{tr}(H\Sigma)$。这些量先回答局部损失怎样被噪声抬高。要解释插值解为什么可能失稳，还要把噪声随残差一起缩小的事实放回去。

## 噪声对齐与稳定性门槛

回到零残差解。越靠近它，噪声越小，扰动还会被放大吗？这里要比的是噪声注入与当前损失的比例。每步哪怕只注入一点，如果它比当前损失还大，反复更新就会出现增长。

为把这个比例和曲率联系起来，在平方损失的非零损失、分母有定义处，用中心化协方差定义

$$
\mu(\theta)=\frac{\operatorname{tr}(\Sigma(\theta)G(\theta))}
{2L(\theta)\|G(\theta)\|_F^2}.
$$

假设相关区域中 $\mu(\theta)\ge\mu_0>0$。这个条件只要求与 $G$ 配对得到的注入足够强，整个协方差矩阵可以有更复杂的形状。

在插值极小值附近线性化，令 $\mathcal L(\delta)=\delta^\top H\delta/2$，此时 $G=H=H(\theta^*)$。对于独立抽样、batch size 为 $B$ 的 SGD，先把一步的线性化损失按平均更新和零均值误差展开。

$$
\mathbb E[\mathcal L(\delta_{t+1})\mid\delta_t]
=\mathcal L\bigl((I-\eta H)\delta_t\bigr)
+\frac{\eta^2}{2B}\operatorname{tr}\bigl(H\Sigma(\delta_t)\bigr).
$$

第一项是沿平均更新走完后的损失，仍然非负。只留下第二项，用对齐下界并取期望，就得到一个可以逐轮重复的估计。

$$
\mathbb E\mathcal L(\delta_{t+1})
\ge q\,\mathbb E\mathcal L(\delta_t),
\qquad
q=\frac{\eta^2\mu_0}{B}\|H\|_F^2.
$$

若沿第 $i$ 个方向的方差与 $L\lambda_i$ 同阶，进入损失时又乘了一次 $\lambda_i$。所以这里积累的是 $\sum_i\lambda_i^2$，Frobenius 范数就从这一步出来了。当 $q>1$ 时，迭代下界给出定理 3.5 的增长结论。 [3]

$$
\boxed{\mathbb E\mathcal L(\delta_t)\ge q^t\mathbb E\mathcal L(\delta_0).}
$$

反过来，若要求对任意小扰动，线性化系统的期望损失始终受初值的常数倍控制，就需要 $q\le1$。解出曲率门槛，得到定理 3.3 的必要条件。 [3]

$$
\boxed{
\|H(\theta^*)\|_F\le\frac1\eta\sqrt{\frac B{\mu_0}}.
}
$$

小于这个门槛只是通过了这项筛选。增长率和门槛都说的是线性化模型的期望损失，真实非线性轨迹的逐条退出与测试性能仍要另看。对齐下界在线性模型和随机特征模型中有理论支持，一般非线性网络的依据主要来自实验。

把公式当成一个旋钮试试。固定 $B,\mu_0$ 时，$\eta$ 越大，允许的 $\|H\|_F$ 越小。固定 $\eta,\mu_0$ 时，增大 batch 会放宽门槛。若只想在 $\mu_0$ 不变的条件下保持这道门槛，应保持 $\eta/\sqrt B$，也就是保持离散放大项里的 $\eta^2/B$。前一节的 $\eta/B$ 则来自动力学的连续时间匹配，控制的是扩散强度。于是，同样的训练 loss 可以对应不同的局部稳定性，接下来要看这些曲率限制何时能落到模型实际表示的函数上。

## 从稳定性到函数复杂度

两个训练误差都为零的解，可以有不同的局部稳定性。即便知道 SGD 排除了其中一个，也还得问，剩下的解在函数上有什么共同点？在对角线性网络和两层 ReLU 网络里，这个问题可以拆成几步。

$$
\text{稳定性}\Longrightarrow\text{曲率约束}
\Longrightarrow\text{函数复杂度约束}
\Longrightarrow\text{测试风险上界}.
$$

先看看曲率这一关。取 $B=1$，用扰动的二阶矩记录各个参数方向怎样变化。

$$
Q_t=\mathbb E[\delta_t\delta_t^\top].
$$

这里要求对任意初始扰动分布和任意 $t$ 都有 $\|Q_t\|_F\le\|Q_0\|_F$。上一节只控制期望损失，这里要求整个二阶矩的 Frobenius 范数不增。标量平方损失在零残差处还有个好处，每个样本的 Hessian 退化为秩一矩阵 $H_i=g_i g_i^\top$。

为了看这条稳定性要求怎样约束总曲率，试着给每个方向同样的初始二阶矩，取 $Q_0=I$。在线性化系统里，把它整体缩小也不会改变下面的比较。做一步后，展开 $(I-\eta H_i)Q_0(I-\eta H_i)$ 并取平均，得到

$$
Q_1=I-2\eta H+\eta^2\mathbb E_i[H_i^2].
$$

稳定性给出 $\|Q_1\|_F\le\sqrt p$，所以 $\operatorname{tr}Q_1\le\sqrt p\|Q_1\|_F\le p$。对上式取迹，秩一的 $H_i$ 有 $\operatorname{tr}(H_i)=\|g_i\|^2$、$\operatorname{tr}(H_i^2)=\|g_i\|^4$，因此

$$
\eta\,\mathbb E_i\|g_i\|^4\le2\mathbb E_i\|g_i\|^2.
$$

再用 $\mathbb E\|g_i\|^4\ge(\mathbb E\|g_i\|^2)^2$ 与 $\operatorname{tr}H=\mathbb E\|g_i\|^2$，就得到命题 3.2 的迹约束。 [4]

$$
\boxed{\operatorname{tr}H(\theta^*)\le\frac2\eta.}
$$

这个推导用的是秩一结构与二阶矩稳定性，没有用到前节的对齐下界。在低损失、光滑性与对齐的假设下，较弱的损失稳定性给出的是 Frobenius 范数界。选择哪条界，要先说明采用的是哪种稳定性定义。

现在来试一个能把曲率读成函数范数的模型。对角线性网络把预测系数 $\beta_j$ 写成两个参数的乘积。

$$
f_\theta(x)=(a\odot b)^\top x=\beta^\top x,
\qquad \beta_j=a_jb_j.
$$

尽管预测是线性的，对参数求导会分别留下 $a_j$ 和 $b_j$。令 $\alpha_j=a_j^2+b_j^2$。在二阶矩标准化的输入分布下，总体版本的 $G$ 的非零特征值正是各个非零的 $\alpha_j$，于是有

$$
\|G\|_2=\|\alpha\|_\infty,
\quad \|G\|_F=\|\alpha\|_2,
\quad \operatorname{tr}G=\|\alpha\|_1.
$$

有限样本的对应关系还要通过概率界来控制。先看总体等式，利用 $a_j^2+b_j^2\ge2|a_jb_j|$，每个坐标都给出一项，合起来有 [4]

$$
\operatorname{tr}G\ge2\|\beta\|_1.
$$

这样，限制 $\operatorname{tr}G$ 就限制了预测函数的 $\ell_1$ 范数。对特定的有界均匀输入分布及可实现线性目标 $f^*(x)=\beta^{*\top}x$，当 $n\gtrsim\log(d/\delta)$ 时，定理 5.3 以至少 $1-\delta$ 的概率对任意满足上述 SGD 线性稳定性的插值解给出 [4]

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

这里 $R$ 是总体平方误差风险，$\lesssim$ 隐去固定常数。学习率通过稳定性给可驻留的插值解加了一道范数限制。至于训练轨迹会在允许的解里选哪一个，仍要看优化动力学。

换成两层 ReLU 网络，再问一次能否把曲率换成函数量。

$$
f_\theta(x)=\sum_{j=1}^m a_j\operatorname{ReLU}(w_j^\top x),
\qquad
P(\theta)=\sum_j|a_j|\|w_j\|.
$$

路径范数 $P(\theta)$ 把每个单元两侧权重尺度的乘积加在一起。对特定球面输入分布，Hessian 的迹与下面的加权平方和联系起来。 [4]

$$
\sum_j(\|w_j\|^2+d a_j^2).
$$

每项都可以用两边尺度的乘积作下界，因此

$$
\sum_j(\|w_j\|^2+d a_j^2)\ge2\sqrt d\,P(\theta).
$$

配合迹约束，SGD 的稳定插值解满足 $P(\widehat\theta_{\mathrm{sgd}})\lesssim1/(\eta\sqrt d)$。在这套分析里，GD 的谱约束给出 $P(\widehat\theta_{\mathrm{gd}})\lesssim1/\eta$。把路径范数上界放进风险估计，在有界可实现目标、上述球面分布和样本量前提下，定理 4.3 对同一学习率 $\eta$ 下的稳定插值解给出以下量级。 [4]

$$
\boxed{
R(\widehat\theta_{\mathrm{sgd}})
\lesssim\widetilde O\left(\frac1{\eta^2n}\right),
\qquad
R(\widehat\theta_{\mathrm{gd}})
\lesssim\widetilde O\left(\frac d{\eta^2n}\right).
}
$$

界里没有显式的网络宽度 $m$。样本量前提仍随输入维数变化，约为 $d^2$ 再乘对数因子，风险对比也固定了两边的学习率。若想在训练中识别这里的筛选，可分别测对角模型的 $\|\beta\|_1$ 或 ReLU 模型的路径范数，再用不同初始化比较尺度的影响。小初始化本身也可能带来偏好，较大初始化的对照有助于把两种作用区分开。上述保证针对写出的模型与分布。

这条推导解释了为什么有些解能留下来。若把学习率提高到当前区域失稳，参数朝哪里走，还得把刚才合在一起的方向重新拆开。

## 逃离不稳定区域时的运动方向

前文的对齐是一个总量。假设我们测到它很高，能不能断定每个方向上的噪声都和曲率匹配？先考虑未中心化的梯度二阶矩 $M$。当分母有定义时，一个量用迹衡量整体配对，另一个量只沿方向 $v$ 看。

$$
\mu_M(\theta)=\frac{\operatorname{tr}(MG)}{2L\|G\|_F^2},
\qquad
g_M(\theta;v)=\frac{v^\top Mv}{2L\,v^\top Gv}.
$$

令 $Gu_i=\lambda_i u_i$。把第一个式子的迹沿着 $G$ 的特征方向展开，每一项都能改写成第二个式子乘以相应权重。

$$
\mu_M=\sum_i\frac{\lambda_i^2}{\sum_j\lambda_j^2}\,g_M(\theta;u_i).
$$

于是整体对齐就是以曲率平方为权重的方向平均。若几个陡峭方向占了大多数权重，整体数值很好也可能只说明这几个方向对齐。要分析逃离的方向，需要单独知道每个相关方向上会发生什么。

在不同模型里，能给出多强的对齐保证，取决于输入和所选方向。下表保留有限样本结果的量级及主要条件。 [5]

| 结果 | 模型与主要条件 | 结论的结构 |
|---|---|---|
| 定理 3.2、4.2 | $f_\theta(x)=F(\theta)^\top x$，高斯输入；样本量约为 $\widetilde O(d^2)$ | 对参数与方向统一控制对齐强度，条件不随参数维数 $p$ 增长 |
| 定理 3.3 | 普通线性模型；输入协方差有足够大的有效维数 | 在更低样本量区间仍可控制整体损失对齐 |
| 定理 3.5 | 固定输出权重的两层网络、高斯输入；$ 0\le\alpha\le\phi'\le\beta$ | 整体损失对齐有与网络宽度无关的上下界，常数依赖 $\alpha,\beta$ |
| 定理 4.3 | 普通线性模型、预先固定的有限组方向 | 方向对齐所需样本量可降至约 $\widetilde O(d)$ |

这里有两处值得连着假设读。正斜率下界适合满足条件的 Leaky ReLU，普通 ReLU 的全参数空间需要另外分析。预先固定的一组方向也有别于从同一训练集估计出来的 Hessian 特征向量。表里的模型允许参数维数 $p$ 很大，对齐保证仍可能由输入维数和样本条件控制。 [5]

再用一个能算到底的例子看 $M$ 和实际噪声的区别。设 $x\sim N(0,I_d)$、$y=w_*^\top x$，令 $e=w-w_*$。从预测残差 $e^\top x$ 出发，有

$$
L=\tfrac12\|e\|^2,\qquad G=I,\qquad b=e.
$$

单样本梯度是 $(e^\top x)x$，用高斯四阶矩可以算出它的未中心化二阶矩。

$$
M=\mathbb E[(e^\top x)^2xx^\top]
=\|e\|^2I+2ee^\top,
$$

现在把平均梯度 $b=e$ 的贡献扣掉，就得到抽样协方差。

$$
\Sigma=M-bb^\top=\|e\|^2I+ee^\top.
$$

记 $\varphi$ 为非零的 $e$ 与 $v$ 的夹角，沿 $v$ 代入，两个比值分别为

$$
g_M(v)=1+2\cos^2\varphi\in[1,3],
\qquad
g_\Sigma(v)=1+\cos^2\varphi\in[1,2].
$$

沿误差方向看，$M$ 的因子可以到 $3$，$\Sigma$ 的因子只到 $2$。垂直于误差时，两者都是 $1$。所以用二阶矩得到的方向对齐，转成真正的噪声假设时，需要检查中心化项怎样影响它。

现在回到插值解附近的线性化模型。令 $G=H(\theta^*)$、$\mathcal L(\delta)=\delta^\top G\delta/2$，并另外要求真实零均值噪声在各特征方向满足

$$
A_1\mathcal L(\delta)\lambda_i
\le\mathbb E[(u_i^\top\xi)^2\mid\delta]
\le A_2\mathcal L(\delta)\lambda_i.
$$

固定 batch 的影响可以吸收到常数里。若只看第一个方向，可能会猜测大部分运动都在最陡处。但我们可以把前 $k$ 个方向和剩余方向分别加总，用损失能量来比。

$$
X_t=\sum_{i\le k}\lambda_i\mathbb E[(u_i^\top\delta_t)^2],
\qquad
Y_t=\sum_{i>k}\lambda_i\mathbb E[(u_i^\top\delta_t)^2].
$$

在上述方向对齐条件下，取 $\eta=\beta/\|G\|_F$ 且 $\beta$ 足够大。对非零初始损失，线性化 SGD 进入不稳定区间。走过定理所需的短暂过渡后，定理 5.2 给出两组能量之比的下界。 [5]

$$
\boxed{
\frac{Y_t}{X_t}\gtrsim
\frac{\sum_{i>k}\lambda_i^2}{\sum_{i\le k}\lambda_i^2}.
}
$$

取 $k=1$ 时，右侧是 $\sum_i\lambda_i^2/\lambda_1^2-1$。试着取 $\lambda_1=10$，其余有一千个特征值等于 $1$。每个小方向都比第一方向平缓，它们的平方和却是

$$
\lambda_1^2=100,\qquad \sum_{i>1}\lambda_i^2=1000.
$$

单个较陡方向上的注入更强，许多相对平缓方向加起来仍可以承载更多能量。这里说的平缓是与顶部方向相比，若 $\lambda_i=0$，对齐假设也给出该方向无这种噪声注入。对于 GD，命题 5.3 的比较条件是 $\eta\lambda_1>2$、$\lambda_1>\lambda_2$，且初始扰动在 $u_1$ 上非零。在这些条件下，最陡方向渐渐主导它的逃离。 [5]

想在日志里找这种差别，可以把位移投到几个谱区间，分别看顶部和其余方向的能量。提高学习率可使当前区域失稳，SGD 的多方向运动提供了沿低损失谷探索的一种解释，之后降低学习率又可恢复稳定。在相应模型和实验中能看到这种机制，判断一次 spike 是否伴随有效探索，还要结合后续曲率、方向和验证集表现。 [5]

上面比较的是离开一个区域时往哪走。还有一类移动，即使预测函数保持一样，参数也能沿着等价表示改变尺度。

## 等价参数化与噪声平衡

看最小的两层模型 $f_{u,v}(x)=uvx$。把一层放大 $c$ 倍、另一层缩小 $c$ 倍，对任何 $c>0$，

$$
(u,v)\longmapsto(cu,v/c)
$$

预测与每个样本的损失都一样。可如果盯着层范数、单层梯度或者 Hessian，数值就可能变了。训练能不能沿着这样一条等价轨道，自己把两层调得更平衡？

设单样本损失只依赖乘积 $uv$，记 $q=\partial\ell/\partial(uv)$。先算连续梯度流。

$$
\dot u=-qv,\qquad \dot v=-qu,
$$

对 $u^2$ 与 $v^2$ 分别求导，结果都是 $-2quv$，相减后恰好消掉。

$$
\frac d{dt}(u^2-v^2)=0.
$$

因此理想梯度流保留初始的层间平方差。把同样的方向改为有限步长再算一次，

$$
u'=u-\eta qv,\qquad v'=v-\eta qu,
$$

两个交叉项依旧抵消，平方项却留了下来。

$$
\boxed{u'^2-v'^2=(1-\eta^2q^2)(u^2-v^2).}
$$

在合适的步长下，只要 $q$ 持续非零，这个因子就会推动平方差缩小。即使取全梯度，有限步也有这个二阶修正。若 $q$ 来自随机抽样，$\mathbb E q^2=(\mathbb E q)^2+\operatorname{Var}(q)$，方差还会改变修正的强度。于是我们找到了一个可以沿等价参数化积累的量。

把例子推广一点，设对称矩阵 $A$ 生成逐样本的指数对称性。

$$
\ell_i(e^{\lambda A}\theta)=\ell_i(\theta),\qquad \forall i,\lambda.
$$

沿 $\lambda$ 求导，得到每个样本梯度都垂直于 $A\theta$。令 $Q(\theta)=\theta^\top A\theta/2$，它的梯度正是 $A\theta$，所以在梯度流里守恒。这就是这种对称性对应的 Noether 量。下面用同一套常数比较权重衰减和噪声，写出 SDE

$$
d\theta=-(\nabla L+2\gamma\theta)\,dt
+\sqrt{2\tau}\,\Sigma(\theta)^{1/2}dW,
\qquad \tau=\frac\eta{2B}.
$$

对 $Q$ 应用 Itô 公式。一阶的任务梯度项因正交性消失，衰减留下 $-4\gamma Q$，噪声的二阶项留下协方差与 $A$ 的配对。

$$
\boxed{\dot Q=-4\gamma Q+\tau\operatorname{tr}(A\Sigma).}
$$

这里 $\dot Q$ 指条件漂移，称为 Noether flow。若无权重衰减，平衡条件就是 $\operatorname{tr}(A\Sigma)=0$。逐样本梯度仍与对称切向正交，噪声引起的漂移来自 Itô 二阶项。这和小例子里一次项抵消、二次项留下的情况相呼应。

接下来沿同一条轨道 $\theta_\lambda=e^{\lambda A}\theta$ 试着移动。如果漂移在某处为零，往两边挪一点会发生什么？用损失的变换关系对参数求导，再将梯度变换代入协方差，有

$$
\Sigma(\theta_\lambda)=e^{-\lambda A}\Sigma(\theta)e^{-\lambda A},
\qquad
\frac d{d\lambda}\operatorname{tr}(A\Sigma(\theta_\lambda))
=-2\operatorname{tr}(A^2\Sigma(\theta_\lambda))\le0,
$$

另一项满足 $\mathrm dQ(\theta_\lambda)/\mathrm d\lambda=\theta_\lambda^\top A^2\theta_\lambda\ge0$。因此两项合起来的漂移随 $\lambda$ 单调不增。定理 4.3 说明固定轨道上存在平衡位置，可能在 $\lambda=\pm\infty$，漂移不退化时位置唯一，协方差足够光滑时有限平衡还具有相应的光滑性。若有非退化的有限根，根两侧的漂移指向恢复平衡的方向。这里的唯一性是在给定轨道上的，训练中轨道和平衡位置都可能移动。对移动平衡的跟踪还要用额外条件。 [6]

用两层线性网络就能看出，平衡究竟要比较哪两个量。写 $f(x)=UWx$，对可逆 $R$，$U\mapsto UR$、$W\mapsto R^{-1}W$ 保持乘积。考虑 $y=V_*x+\epsilon$，输入和零均值标签噪声独立，噪声非退化，且网络已经实现 $UW=V_*$、不加权重衰减。用 $\Sigma_x,\Sigma_\epsilon$ 表示输入和输出噪声的协方差，在定理 5.2 的这个特例中，漂移为零的条件变成 [6]

$$
\boxed{
W\overline\Sigma_xW^\top
=U^\top\overline\Sigma_\epsilon U,
\qquad
\overline\Sigma=\frac\Sigma{\operatorname{tr}\Sigma}.
}
$$

左边是输入通过第一层到隐藏空间后的结构，右边是输出噪声反传到隐藏空间后的结构。若两种协方差都是各向同性的，归一化后分别只留下 $I/d_x$ 和 $I/d_y$，于是

$$
\frac{WW^\top}{d_x}=\frac{U^\top U}{d_y}.
$$

即便到了各向同性，也要把输入和输出的维数算进去，特定的维数与尺度下才简化为 Gram 矩阵相等。再加中间层，定理 5.4 构造的一类噪声平衡解，在有效秩子空间中让中间层的非零奇异值拥有相同尺度，两端仍按输入和输出噪声协方差加权。隐藏空间里的正交自由度继续保留。 [6]

我们还能回到前面用过的曲率指标试一次。在这类两层线性模型的平方损失下，Hessian 迹为

$$
\operatorname{tr}H
=d_y\|W\Sigma_x^{1/2}\|_F^2
+\operatorname{tr}(\Sigma_x)\|U\|_F^2.
$$

沿等价轨道缩放 $U,W$，两项可以朝不同方向变化。噪声平衡由 $\dot Q=0$ 决定，平衡附近的迹可能比出发时更大或更小，取决于数据、噪声和初始尺度。稳定性是在某处问扰动能否留下来，这里则是在同一个函数的表示之间问尺度会往哪移。因此看层间平衡时，可以一并记录层范数、激活协方差与曲率，并在比较 sharpness 时说明参数化和尺度约定。

归一化会改变这些坐标及局部条件数，所以从平衡角度观察它比只看训练 loss 更细。早期较小的步长也可能给层间尺度留出调整的时间，这是理解 warmup 的一个实验线索，具体是否变平或变尖仍依赖起点。若已经精确插值、每个样本的梯度都为零，又没有衰减，噪声驱动本身也消失了。

到这里，噪声能在梯度流里留下额外的二阶作用。反过来问一句，若抽样噪声已经拿掉，训练里的振荡还会不会发生？

## 自适应优化器的动力学

把 batch 放大到全数据，抽样误差消失，loss 还会突然抬头吗？Adam 的分母也在更新。只要历史二阶统计的反应速度和参数移动不同，即便梯度由全数据计算，每一步走多远也可能变化很大。先把这套状态写出来。

$$
m_{t+1}=\beta_1m_t+(1-\beta_1)g_t,
\qquad
v_{t+1}=\beta_2v_t+(1-\beta_2)g_t^{\odot2},
$$

$$
\theta_{t+1}=\theta_t-\eta
\frac{\widehat m_{t+1}}{\sqrt{\widehat v_{t+1}}+\varepsilon}.
$$

帽号表示偏差修正，运算按坐标进行。这一节主要看全 batch、固定学习率时的连续极限和离散行为。对应实验有平方损失和分类任务，也有部分大 batch 随机 Adam 的观察。小 batch 情况还要把抽样误差放回来。

先看 $\eta$ 很小时，动量还能记住多远。若 $\beta_1,\beta_2\in(0,1)$ 固定，一阶和二阶动量记住的大致是固定数量的更新步。但用 $t=k\eta$ 计时，每一步代表的时间越来越短，这段记忆对应的连续时间也趋于零。假设目标梯度有界且 Lipschitz 连续、$\varepsilon>0$ 固定，令 $\eta\to0$。命题 1 给出 Adam/RMSprop 在任意固定有限时间区间上的极限。 [7]

$$
\boxed{\dot\theta=-\frac{\nabla L(\theta)}{|\nabla L(\theta)|+\varepsilon}.}
$$

一阶状态跟踪当前梯度，二阶状态的平方根跟踪梯度的绝对值。某个梯度坐标的绝对值远大于 $\varepsilon$ 时，大小基本被分母约掉，对应近似为

$$
\dot\theta=-\operatorname{sign}(\nabla L(\theta)).
$$

梯度接近零时，$\varepsilon$ 仍然决定精确极限。于是另一种取法也有意义。希望动量保留固定的连续时间记忆，就得让它记住的步数随 $\eta$ 变小而增加，取

$$
\beta_1=1-b\eta,\qquad \beta_2=1-a\eta,
\qquad a,b>0,
$$

在相应光滑性条件与零初始动量等假设下，命题 2 的极限保留了两个状态。先算动量统计怎样追上当前梯度。 [7]

$$
\dot m=b(\nabla L-m),\qquad
\dot v=a((\nabla L)^{\odot2}-v),
$$

再把偏差修正放进参数的速度。

$$
\dot\theta=-\frac{m/(1-e^{-bt})}
{\sqrt{v/(1-e^{-at})}+\varepsilon}.
$$

这里的 $a,b$ 决定两种统计在连续时间中的响应速度。命题 3 还说明，在初始各梯度坐标远离零、$\varepsilon=0$ 等条件下，即便保留动量，最初短时间的速度也接近 signGD，偏差有随时间线性增长的上界。看一个连续模型时，要先看它采用了哪一种动量与学习率的缩放。 [7]

理想的符号更新为什么能很快降损失？假设目标满足 Polyak–Łojasiewicz 条件

$$
\|\nabla L(\theta)\|_2^2\ge
\mu_{\mathrm{PL}}(L(\theta)-L_*),\qquad \mu_{\mathrm{PL}}>0.
$$

只要损失还高于最优值，这个条件就给梯度范数一个下界。它也可以用于符合条件的非强凸目标。令 $h(t)=L(\theta(t))-L_*$，在理想 signGD 流中求导，损失下降率恰好是梯度的 $\ell_1$ 范数的负值。在 $h>0$ 时，

$$
\dot h=-\|\nabla L\|_1
\le-\|\nabla L\|_2
\le-\sqrt{\mu_{\mathrm{PL}}h},
\qquad
\frac d{dt}\sqrt h\le-\frac{\sqrt{\mu_{\mathrm{PL}}}}2.
$$

这时跟踪 $\sqrt h$ 比跟踪 $h$ 更直接，因为它至少以一个固定速度下降。积分得到命题 4 的时间界。 [7]

$$
\boxed{
h(t)\le\left(\sqrt{h(0)}-\frac{\sqrt{\mu_{\mathrm{PL}}}}2t\right)^2,
\qquad
T_*\le2\sqrt{\frac{h(0)}{\mu_{\mathrm{PL}}}}.
}
$$

到达后保持在最优值，若写成全时域的式子，可取括号的正部。这个推导解释了理想连续流的有限时间下降。离散训练每次移动有限距离，到了目标附近要另算会不会越过它。

回到驻点附近的全 batch RMSprop。若 $\sqrt v$ 相对于 $\varepsilon$ 已经很小，分母便主要由 $\varepsilon$ 决定，一步近似为

$$
\theta_{t+1}\approx\theta_t-\frac\eta\varepsilon\nabla L(\theta_t).
$$

预备知识里那道一维稳定性条件此时又用得上，只是乘在梯度前面的量成了 $\eta/\varepsilon$。无一阶动量时，在局部二次模型中的稳定性约束近似为

$$
\eta\lambda_{\max}(H)\lesssim2\varepsilon.
$$

固定 $\eta$、把 $\varepsilon$ 设得很小时，这个约束很苛刻。Adam 的一阶动量也参与定点附近的更新，精确边界还会依赖动量参数。

可以直接算一个停不下来的轨道。取 $L(x)=x^2/2$ 和 $\varepsilon=0$。在所讨论的 RMSprop 递推里，若从下面这组状态起步，

$$
x_t\in\left\{\frac\eta2,-\frac\eta2\right\},
\qquad v_t=\frac{\eta^2}{4}.
$$

两个位置的梯度平方都等于 $\eta^2/4$，二阶状态保持原值。分母约掉梯度的大小，每次恰好走长度 $\eta$，于是来回跳，loss 停在 $\eta^2/8$。这个例子给出了一个二周期，也让我们看到全梯度下的振荡可以怎样从更新式里产生。高维训练是否出现这种行为还要看目标与状态。

真实的两个动量统计并不会一直刚好匹配梯度。沿用 $a=(1-\beta_2)/\eta$、$b=(1-\beta_1)/\eta$，可以看分子和分母各自对新梯度反应多快。实验里观察到三个典型区间。 [7]

| 时间尺度关系 | 实验中的典型行为 |
|---|---|
| $b$ 显著大于 $a$ | 可能反复出现较大 spike |
| $a$ 与 $b$ 接近 | 通常为幅度较小、较快的振荡，训练较平稳 |
| $a$ 显著大于 $b$ | 可能进入发散区域 |

例如 $\beta_1=0.9,\beta_2=0.999$ 时，$b/a=100$，分子跟踪得比二阶统计快得多。所测任务里，使两种时间尺度更接近可以减轻后期 spike，在追求较低训练误差的函数拟合和 PDE 求解中尤其有用。这个分区来自相应全 batch、固定学习率等实验设置。小 batch、交叉熵、AdamW 或大模型要分别验证。 [7]

若想判断一次 spike 从何而来，可以固定数据、关闭额外随机源，看看全 batch 或大 batch 对照中能否复现。复现时再看真正的更新 $\eta\widehat m/(\sqrt{\widehat v}+\varepsilon)$、相对参数的大小和分母分布。只记录 $\|g\|$ 看不到这些量。高精度回归里，学习率、两个动量时间尺度和 $\varepsilon$ 可以一起影响后期振荡。增大 $\varepsilon$ 也会改动有效预条件，因而同样需要观察实际更新。

## 训练中的曲率与噪声测量

读完前面的例子，再碰到一条 loss 曲线抬头，先问能从 checkpoint 里量到什么。对自适应方法，原始 Hessian 还要经过预条件。为了看清这一点，暂时固定某一时刻的正定对角矩阵 $P$，把动量的变化放在下一步考虑。预条件 GD 的局部扰动满足

$$
\delta_{t+1}=(I-\eta PH)\delta_t.
$$

$PH$ 与对称矩阵 $P^{1/2}HP^{1/2}$ 相似。于是，在局部 $H\succeq0$ 时，前面的一维判据要逐个应用到这个对称矩阵的谱，最大方向对应

$$
\eta\lambda_{\max}(P^{1/2}HP^{1/2})
$$

若原始抽样协方差为 $\Sigma$，乘上 $P$ 后就变成 $P\Sigma P$。真实 Adam 的 $P_t$ 还在随梯度和动量变化。固定 $P$ 的计算只帮我们拆出预条件的作用，也提示比较两种优化器时要量处理后的方向和尺度。

显式存储 $p\times p$ 的 $H$ 很贵。假如手边只有 Hessian–vector product（HVP），还能读出前面用到的哪些曲率？取满足 $\mathbb E[zz^\top]=I$ 的随机探针 $z$。把二次型写成迹再取期望，有

$$
\mathbb E[z^\top Hz]=\operatorname{tr}H,
\qquad
\mathbb E\|Hz\|^2=\|H\|_F^2.
$$

因此一次 HVP 就能同时给迹和 Frobenius 范数平方各一个样本。多取几个探针可作估计，最大特征值则可通过基于 HVP 的迭代估计。实际精度取决于探针数、谱形状和数值误差。

噪声也可以在同一个 checkpoint 里测。先固定参数，独立采集 $K\ge2$ 个大小为 $B$ 的 batch 梯度 $\widehat g^{(k)}$，以 $\overline g$ 为它们的平均。在有放回独立抽样模型下，先估计 batch 梯度的协方差，再乘 $B$ 还原单样本协方差。

$$
\widehat\Sigma=
\frac B{K-1}\sum_{k=1}^K
(\widehat g^{(k)}-\overline g)(\widehat g^{(k)}-\overline g)^\top.
$$

若想知道噪声把多少能量放在高曲率方向，不必形成整个 $\widehat\Sigma$。令 $d_k=\widehat g^{(k)}-\overline g$，把每个外积与 $H$ 的迹化成一次二次型。

$$
\widehat{\operatorname{tr}(H\Sigma)}
=\frac B{K-1}\sum_k d_k^\top H d_k.
$$

额外的 batch 梯度和 HVP 适合在若干 checkpoint 上做诊断。固定参数是为了让 $d_k$ 只反映抽样差异。若一边更新一边采样，差异里还会混入轨迹自身的变化。远离极小值时 $H$ 可能不定，迹可以正负抵消，$\operatorname{tr}(H\Sigma)$ 也可能为负。需要正半定的曲率代理时，应明确采用的是 $G$ 还是真实 $H$。

这样，开头那个问题可以落到几种不同的检查上。若关心什么样的解能驻留，比较局部曲率和扰动。若怀疑噪声在推动参数离开，量它在各谱区间的投影。若输出变化不大但层范数还在动，检查等价参数化中的尺度。再遇到 loss spike，就可以用实际更新与这些量作对照，看看究竟是哪一部分在变化。

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
