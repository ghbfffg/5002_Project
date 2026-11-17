# Yellow Code: A Data-Driven Look at NYC Taxi Trips

## Presentation Script / 演讲稿

建议时长：8–9 分钟。演讲时按照 poster 从上到下、从左到右移动。

---

# 中文版

## 开场：研究问题（约 1 分钟）

大家好，我们的项目题目是 **Yellow Code: A Data-Driven Look at NYC Taxi Trips**。

我们想研究的问题是：**出租车记录中的小费，究竟反映了乘客对行程的评价，还是更多反映了账单金额、支付方式和行程情境？**

小费看起来像是对司机服务的直接评价，但一笔小费同时受到很多因素影响：乘客看到的金额、支付界面提供的选择、行程是否变慢，以及乘客如何理解这次延误。

因此，我们没有把小费简单地当成“满意度分数”，而是把它当作一种行为记录，观察它在不同条件下如何变化。

## 数据与方法（约 1 分钟）

我们使用纽约 TLC 的 Yellow Taxi 行程数据，主要包括 2024 年 12 月和 2025 年 1 月，共 **714 万条原始记录**。

数据包含上下车时间、行程距离、Taxi Zone、车费、附加费、支付方式和小费金额。小费分析主要使用信用卡行程，因为现金支付中的现金小费通常不会记录在 `tip_amount` 里。

我们清理了异常时间、负金额、非正车费、零距离和异常时长记录，并定义了两个重要变量：

第一，使用不含小费的账单金额计算小费率。第二，用相对慢度衡量行程是否比相似距离的典型行程更慢。这个慢度只是服务质量的代理变量，不是乘客真实的服务评价。

整个分析包括三条结果线：账单金额、小费金额模式，以及行程慢度和天气等情境因素。

## 发现一：账单越大，百分比模式越少（约 1.5 分钟）

请看第一栏的两张图。

我们首先检查小费金额是否接近 15%、20% 或 25% 的账单比例。这个分类只能说明金额模式接近这些比例，不能证明乘客确实点击了支付终端上的按钮，因为数据中没有点击日志。

在所有 January 信用卡行程中，大约 **60.6%** 的记录匹配至少一种候选百分比，单独匹配 20% 的记录约占 **49.1%**。

但这种模式会随着账单金额变化。税前账单在 12 到 16 美元时，匹配比例达到 **65.8%**；到了 40 到 50 美元，下降到 **42.8%**；在 80 到 100 美元时，约为 **30.7%**。

第二张图显示，在没有匹配这些百分比的记录中，小额账单更常出现正好 1 美元或 2 美元的小费。账单变大后，1 美元和 2 美元小费减少，零记录信用卡小费在 40 到 50 美元区间上升到约 **31.3%**。

这里的重点不是说乘客突然变得更吝啬，而是：**账单金额可能改变了乘客采用哪一种小费规则。** 有些人使用比例，有些人使用固定金额，还有一些人不留下可记录的小费。

## 发现二：默认百分比选项可能削弱小费的满意度信号（约 1.5 分钟）

第二栏比较相对行程速度与小费率，想回答一个更直接的问题：**当支付界面已经提供了百分比小费选项时，小费还能够多大程度反映顾客对服务的满意程度？**

我们把每次行程的时长与相似距离行程的典型时长进行比较，分成八个慢度区间。相对慢度越高，表示这次行程比同距离行程更慢。

在百分比匹配记录中，平均小费率从最快组的 **20.30%** 变化到最慢组的 **20.53%**，基本保持不变。也就是说，行程变慢之后，记录中的小费金额仍然被固定在相近的百分比附近。

但在其他金额模式记录中，平均小费率从 **15.20%** 降到 **7.58%**。最慢的一组中，约 **50.8%** 没有记录信用卡小费。

这说明，当默认选项把支付行为引导到一个百分比时，小费可能已经不再充分反映顾客对具体服务的评价。乘客可以完成支付，但小费金额未必随着体验变化。

我们需要谨慎解释这一点。百分比匹配组本来就是按照金额模式筛选出来的，并不是随机分组，所以不能直接说默认按钮因果地消灭了服务反馈。

更稳妥的结论是：**默认百分比选项可能削弱小费作为满意度信号的作用。小费记录不只是顾客评价的结果，也受到支付界面和金额选择规则的影响。**

## 发现三：延误与小费的关系取决于情境（约 2 分钟）

第三栏进一步研究：如果行程变慢，乘客是否一定会减少小费？

我们只在其他金额模式记录中分析这个问题，并加入天气和记录中的乘客人数信息。这里的乘客人数有缺失和误报，所以 poster 中使用的是“记录为单人或缺失”和“记录为两人以上”，而不是绝对准确的真实人数。

第一张图比较极慢行程和正常行程的小费率差异。

在记录为单人或缺失的行程中，未达到强降水阈值时，极慢行程的小费率低 **4.04 个百分点**；在强降水时，差异缩小到 **2.89 个百分点**。

记录为两人以上时，差异要小得多，分别约为 **−0.57** 和 **−0.73 个百分点**。

这与一个有趣的行为解释一致：乘客可能会区分“司机造成的延误”和“天气造成的延误”。如果天气让所有交通都变慢，乘客可能减少对司机的惩罚。

第二张图显示，这种差异主要集中在较高金额的行程。最高账单五分位中，记录为单人或缺失的极慢行程比正常行程低约 **6.53 个百分点**；最低五分位则接近零，甚至略为正。

这说明延误的影响不是所有行程都一样。账单越高，小费金额留下的调整空间通常也越大，所以乘客更可能通过小费表达差异。

不过，这些结果只能说与“情境归因”一致，不能说我们直接观察到了乘客的心理，也不能证明天气本身造成了宽容。

## 结论与局限（约 1 分钟）

把三条结果放在一起，我们的结论是：**小费是一种行为痕迹，而不是直接的满意度或心理测量。**

它同时受到账单金额、金额选择方式、相对行程时长以及天气和同行情境的影响。

我们需要强调几个局限。第一，现金小费不可观测。第二，数据没有支付终端的点击日志，所以百分比匹配只能作为金额模式代理。第三，`passenger_count` 不完全可靠。第四，天气、慢度和同行人数都是行为代理，不是问卷中的心理变量。最后，当前情境模型还需要进一步加入账单金额控制、路线控制和更合适的聚类标准误。

所以，我们不是说“乘客一定这样想”，而是说：**这些可观察行为模式，与乘客会根据金额规则和行程情境调整小费的解释相一致。**

谢谢大家。

---

# English Version

## Opening: Research Question (about 1 minute)

Hello everyone. Our project is titled **Yellow Code: A Data-Driven Look at NYC Taxi Trips**.

Our main question is: **What does a recorded taxi tip actually measure? Is it mainly a passenger’s evaluation of the ride, or is it also shaped by the bill, the payment format, and the travel context?**

A tip looks like a direct judgment of the driver. However, the amount may also depend on the number shown on the screen, the choices offered by the payment interface, whether the trip was unusually slow, and how the passenger interprets the delay.

For this reason, we do not treat the tip as a pure satisfaction score. We treat it as a behavioral trace and examine how it changes across different conditions.

## Data and Methods (about 1 minute)

We use New York City TLC Yellow Taxi trip records, mainly from December 2024 and January 2025. The two files contain **7.14 million raw trips**.

The data include pickup and drop-off times, trip distance, Taxi Zones, fare components, payment type, and tip amount. For tip analysis, we focus on credit-card trips because cash tips are generally not recorded in `tip_amount`.

We remove invalid timestamps, negative amounts, non-positive fares, zero-distance trips, and implausible durations. We then construct two important variables.

First, we calculate the tip rate relative to the amount before tip. Second, we measure relative slowdown by comparing each trip’s duration with the typical duration of trips at a similar distance. This slowdown measure is a proxy for service conditions, not a direct survey measure of service quality.

Our results are organized around three aspects: the size of the bill, the pattern of the tip amount, and the travel context surrounding a delay.

## Finding 1: Percentage Patterns Fade as the Bill Grows (about 1.5 minutes)

Please look at the first column.

We first examine whether the recorded tip is close to 15%, 20%, or 25% of the amount before tip. This identifies an amount pattern; it does not prove that a passenger actually pressed a button, because the dataset contains no payment-terminal click logs.

Across January credit-card trips, about **60.6%** match at least one of these candidate percentages, and about **49.1%** match 20%.

However, the pattern changes with the bill. The matching share reaches **65.8%** for bills between 12 and 16 dollars. It falls to **42.8%** for bills between 40 and 50 dollars, and to about **30.7%** for bills between 80 and 100 dollars.

The second figure looks at records that do not match these percentage patterns. At lower bills, exact one-dollar and two-dollar tips are common. As the bill increases, these fixed-dollar tips become less common, while the share with no recorded card tip rises to about **31.3%** in the 40-to-50-dollar range.

The main point is not simply that passengers become less generous. Rather, **the bill may change which tipping rule is used**. Some passengers use a percentage, some use a fixed dollar amount, and some leave no observable card tip.

## Finding 2: Default Percentage Options May Weaken the Satisfaction Signal (about 1.5 minutes)

The second column compares relative trip speed with tip rate and asks a more direct question: **when the payment interface offers percentage-based tip options, how much can the recorded tip still reflect customer satisfaction?**

We divide trip duration by the typical duration of trips in a similar distance band, and then group trips into eight relative-speed categories. A higher slowdown means that the trip took longer than comparable trips.

For percentage-matching records, the mean tip rate is almost flat: it changes from **20.30%** in the fastest group to **20.53%** in the slowest group. In other words, after a slower trip, the recorded tip remains close to the same percentage.

For other-pattern records, the mean tip rate falls from **15.20%** to **7.58%**. In the slowest group, about **50.8%** have no recorded card tip.

This suggests that when a default option directs the payment toward a percentage, the recorded tip may no longer fully reflect how the customer evaluated the specific ride. The passenger can complete the payment, while the amount does not move much with the experience.

We should be careful here. The percentage-matching and other-pattern groups are selected from the observed tip amounts; they are not randomly assigned groups. Therefore, we cannot claim that a default button causally removed service feedback.

The safer conclusion is: **default percentage options may weaken the tip as a satisfaction signal. A recorded tip is shaped not only by the customer’s evaluation, but also by the payment interface and the amount-selection rule.**

## Finding 3: The Delay Association Depends on Context (about 2 minutes)

The third column asks whether a slower ride always leads to a lower tip.

We focus on other-pattern records and compare heavy-precipitation conditions with lower-precipitation conditions. We also use recorded passenger count, but passenger count contains missing and potentially inaccurate values. Therefore, the poster labels the groups as “recorded solo / missing” and “recorded 2+ passengers.”

The first figure compares extremely slow trips with normal trips.

For recorded-solo or missing-passenger records, the extreme-minus-normal tip-rate gap is **−4.04 percentage points** under lower precipitation. Under heavy precipitation, the gap becomes smaller, at **−2.89 percentage points**.

For records with two or more passengers, the gaps are much smaller: approximately **−0.57** and **−0.73 percentage points**.

This pattern is consistent with a context-sensitive interpretation. Passengers may distinguish between a delay that appears attributable to the driver and a delay that appears attributable to the weather. When weather slows traffic more generally, the penalty may become weaker.

The second figure shows that the difference is concentrated in more expensive rides. In the highest bill quintile, the recorded-solo or missing group shows an extreme-minus-normal gap of about **−6.53 percentage points**. In the lowest quintile, the difference is close to zero and slightly positive.

This means that delays do not have the same association with tips for every ride. Larger bills may leave more room for passengers to express a judgment through the tip amount.

Still, these results are only consistent with contextual attribution. We do not directly observe what passengers thought, and we do not prove that weather caused passengers to become more forgiving.

## Conclusion and Limitations (about 1 minute)

Taken together, our findings suggest that **a recorded tip is a behavioral trace, not a direct measurement of satisfaction or psychology**.

It reflects the bill, the amount-selection pattern, the relative duration of the trip, and the surrounding travel context.

There are several important limitations. First, cash tips are not observed. Second, the data do not contain payment-terminal click logs, so percentage matching is only a proxy for an amount pattern. Third, passenger count is not fully reliable. Fourth, slowdown, weather, and passenger grouping are behavioral proxies rather than direct psychological measures. Finally, the current context model still needs stronger controls for bill amount and route, as well as more appropriate clustered standard errors.

Therefore, we are not claiming that passengers definitely thought a particular way. Our claim is narrower: **the observed patterns are consistent with passengers adjusting their tipping behavior according to the amount rule and the context of the trip.**

Thank you.
