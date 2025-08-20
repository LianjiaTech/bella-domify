## 文章编号 : 1003-0077 ( 2022 ) 09-0001-18

## 中文文本自动校对综述

李云汉 1,2 , 施运梅 1,2 , 李 宁 1,2 , 田英爱 1,2

( 1. 北京信息科技大学 网络文化与数字传播北京市重点实验室 , 北京 100101 ; 2. 北京信息科技大学 计算机学院 , 北京 100101 )

关键词 : 自动校对 ; 拼写错误 ; 语法错误 ; 语义错误 ; 数据集 ; 评估指标

摘 要 : 文本校对在新闻发布 、 书刊出版 、 语音输入 、 汉字识别等领域有着极其重要的应用价值 , 是自然语言处理领 域中的-个重要研究方向 。 该文对中文文本自动校对技术进行了系统性的梳理 , 将中文文本的错误类型分为拼写 错误 、 语法错误和语义错误 , 并对这三类错误的校对方法进行了梳理 , 对中文文本自动校对的数据集和评价方法进 行了总结 , 最后展望了中文文本自动校对技术的未来发展 。

中图分类号 :

TP391

文献标识码 : A

## ASurveyofAutomaticErrorCorrectionofChineseText

LiYunhan 1,2 , ShiYunmei 1,2 , LiNing 1,2 , TianYing􀆳ai 1,2

2.SchoolofComputer , BeijingUniversityofInformationTechnology , Beijing100101 , China )

( 1.BeijingInformationScienceandTechnologyUniversity , BeijingKeyLaboratory ofInternetCultureDigitalDissemination , Beijing100101 , China ;

Abstract : Textcorrection , animportantresearchfieldin NaturalLanguage Processing ( NLP ), isofgreat applicationvalueinfieldssuchasnews , publication , andtextinput.Thispaperprovidesasystematicoverviewof automaticerrorcorrectiontechnologyforChinesetexts.ErrorsinChinesetextsaredividedintospellingerrors , grammaticerrorsandsemanticerrors , andthemethodsoferrorcorrectionforthesethreetypesarereviewed.Moreover , datasetsandevaluationmethodsofautomaticerrorcorrectionforChinesetextsaresummarized.Intheend , prospectsfortheautomaticerrorcorrectionforChinesetextsareraised.

Keywords : automaticcorrection ; spellingerrors ; grammaticalerrors ; semanticerrors ; datasets ; evaluationindicators

讯飞实验室发布的飞鹰智能文本校对系统等

早期中文自动校对方法主要基于统计和规则相 结合的方法 [1-2] , 采用了分词 、 统计语言模型 、 统计机 器翻译 ( StatisticalMachineTranslation , SMT ) 和混淆字 符集等技术 。 随着深度学习的发展 , -系列端到端的 方法在自然语言处理 ( NaturalLanguageProcessing , NLP ) 领域逐渐得到应用 , 如循环神经网络 ( Recurrent NeuralNetwork , RNN )、 序列到序列模型 ( Sequenceto-sequence , Seq2seq ) [3-4] 、 注意力机制 [5-6] 、 卷积序列 到序列模型 ( ConvolutionalSequencetoSequence , ConvS2S ) [7] 和基于自注意力的 Transformer 模 型 [8] , 中文文本自动校对研究逐渐从基于规则和统

。

## 0 引言

中文文本自动校对是自然语言处理技术的-个 重要应用方面 。 随着互联网与信息技术的高速发 展 , 中文文本数量呈爆炸式增长 , 这对传统的手工校 对方式提出了严峻挑战 。 为了降低手工校对工作 量 , 中文文本自动校对相关的研究工作得到了人们 的重点关注 。 中文文本自动校对研究始于 20 世纪 90 年代 , 相对于英文文本自动校对研究开始较晚 , 但其发展速度快且取得了丰硕的研究成果 , 目前也 出现了已经商业化的产品 , 如黑马校对软件 、 哈工大

收稿日期 : 2021-10-07 定稿日期 : 2021-11-25 基金项目 : 国家重点研发计划项目 ( 2018YFB1004100 )

计语言模型相结合的方法转向基于深度模型的方 法 , 并且使用序列标注模型 、 神经机器翻译模型 ( NeuralMachineTranslation , NMT ) 和预训练语言 模型进行端到端的校对 。

本文概述了中文文本中的常见错误类型 , 分析 了中文文本校对技术的研究发展现状 , 对中文文本 校对共享任务数据集以及校对系统的评估指标进行 了归纳总结 , 最后探讨了中文文本自动校对技术未 来发展的方向 。

## 1 中文文本的错误类型

中文文本产生的错误可大体分为拼写错误 、 语 法错误和语义错误三类 。

拼写错误 张仰森等人 [9-10] 和 Liu 等人 [11] 指出 音似 、 形似字错误是中文文本中常见的拼写错误 。 形似字错误主要发生在五笔输入和字符识别 ( Optical CharacterRecognition , OCR ) 过程中 , 音似错误则主要 发生在拼音输入和语音识别 ( AutomatedSpeechRecognition , ASR ) 过程中 。 其中 , 音似错误又可以进- 步细分为同音同调 、 同音异调和相似音错误 [12-13] 。 虽 然大部分拼写错误是由音似 、 形似字误用导致 , 但也 有些错误是由于缺少常识性知识或语言学知识所导 致的 , 如表 1 所示 。

表 1 常见拼写错误举例

| 错误类型   | 错误类型   | 错误                    | 正确                     |
|--------|--------|-----------------------|------------------------|
| 形似字错误  | 形似字错误  | 诞续                    | 延续                     |
|        | 同音 同调  | 火势向四周漫 ( man4 ) 延     | 火 势 向 四 周 蔓 ( man4 ) 延 |
| 音似 字错  | 同音 异调  | 但是不行 ( xing2 ) 还是 发生了 | 但是不幸 ( xing4 ) 还是发生了   |
| 误      | 相似 音   | 词青 ( qing1 ) 标注       | 词性 ( xing2 ) 标注        |
|        |        | 知识型错误 埃及有金子塔          | 埃及有金字塔                 |
| 推断型错误  | 推断型错误  | 他的求胜欲很强 , 为了 越狱在挖洞    | 他的求生欲很强 , 为了越狱在挖洞      |

语法错误 NLPTEA 等 [14-20] 语法错误校对竞 赛将中文文本常见语法错误归纳为字词冗余错误 ( Redundantwords , R )、 字词缺失错误 ( Missing words , M )、 搭配不当错误 ( Selectionerrors , S ) 和字 词乱序错误 ( Wordorderingerrors , W ), 如表 2 所示 。

表 2 常见语法错误举例

| 错误 类型   | 错误                   | 正确                  |
|---------|----------------------|---------------------|
| 字词 冗余   | 我根本不能理解这妇女 辞职回家的现象 。 | 我根本不能理解妇女辞职 回家的现象 。 |
| 字词 缺失   | 我河边散步的时候 。           | 我在河边散步的时候 。         |
| 搭配 不当   | 还有 其 他 的 人 也 受 被害 。  | 还有其他的人也受伤害 。        |
| 字词 乱序   | 世界上每天由于饥饿很 多人死亡 。    | 世界上每天很多人由于饥 饿死亡 。   |

语义错误 语义错误是指-些语言错误在字词 层面和语法搭配上不存在问题 , 而是在语义层面上 的搭配有误 [21] , 如表 3 所示 。 由于语义错误的处理 需要模型理解上下文的语义信息 , 因而对模型提出 了较高的要求 , 其校对难度要高于拼写错误校对和 语法错误校对 。

表 3 常见语义错误举例

| 错误类型   | 错误            | 正确                  |
|--------|---------------|---------------------|
|        | 知识错误 中国的首都是南京 | 中国的首都是北京            |
|        | 他戴着帽子和皮靴就 出门了 | 搭配错误 他戴着帽子穿着皮靴就 出门了 |

下文中将分别对拼写错误 、 语法错误和语义错 误的自动校对方法进行总结与分析 。

## 2 中文文本自动校对方法

## 2.1 拼写错误校对方法

中文文本拼写校对流程大致可以分为以下三 步 : ① 错误识别 : 判断文本是否存在拼写错误 , 并 标记出错误位置 ; ② 生成纠正候选 : 利用混淆字符 或通过模型生成字符等方法构建错误字符的纠正候 选 ; ③ 评估纠正候选 : 利用某种评分函数或分类器 等 , 结合局部乃至全局特征对纠正候选排序 , 排序最 高的纠正候选作为最终校对结果 。 事实上 , 大部分 校对方法的流程都可以划分为上述三步 , 不过也有 部分方法 , 如基于深度模型端到端的校对方法 , 将错 误识别阶段省略 , 但本质上也属于此流程 。

中文拼写错误校对早期采用的主要是规则和统 计语言模型 ( StatisticalLanguage Model , SLM ) 相 结合的校对方法 , 该类方法使用规则和统计语言模 型进行检错 , 在生成候选阶段利用混淆字符或通过

2.1.1 基于规则和统计语言模型结合的校对方法

模型生成字符的方式得到纠正候选字符 , 最后通过 统计语言模型进行纠正候选的评估 , 其中 , 校对规则 主要使用了混淆字符集 、 基于分词的查错规则和

校对词典等 , 统计语言模型主要使用了 N 元语法 ( N -gram )、 条 件 随 机 场 ( Conditional Random Fields , CRF ) 等 , 如表 4 所示 。

表 4 基于规则和统计的拼写校对方法

| 引用           | 语言   | 规则                      | 统计模型                |
|--------------|------|-------------------------|---------------------|
| [ 22 ], 1995 | 繁体   | 混淆字符集                   | Bi-gram             |
| [ 23 ], 1998 | 简体   | 最长匹配分词                  | Tri-gram            |
| [ 24 ], 2001 | 简体   | -                       | 互信息                 |
| [ 25 ], 2002 |      | 混淆字符集 , 最小编辑距离          | Tri-gram , 贝叶斯分类器   |
| [ 26 ], 2006 | 简体   | 非多字词错误查错规则              | 互信息                 |
| [ 27 ], 2012 | 繁体   | 形似字符集                   | Bi-gram , 线性回归      |
| [ 28 ], 2013 | 繁体   | 混淆字符集                   | Bi-gram , 线性回归      |
| [ 29 ], 2013 | 繁体   | 混淆字符集 , E-HowNet        | N -gram             |
| [ 30 ], 2013 | 繁体   | 混淆字符集 , 混淆字符替换规则        | N -gram             |
| [ 31 ], 2013 | 繁体   | 混淆字符集 , 校对词典            | Tri-gram , CRF      |
| [ 32 ], 2013 | 繁体   | 混淆字符集                   | N -gram             |
| [ 33 ], 2013 | 繁体   | -                       | 最大熵                 |
| [ 34 ], 2013 | 繁体   | 混淆字符集 , 词典              | SMT , N -gram , SVM |
| [ 35 ], 2013 | 繁体   | 校对词典 , 检错规则             | SMT , N -gram       |
| [ 36 ], 2014 | 繁体   | 混淆字符集                   | Tri-gram            |
| [ 37 ], 2014 | 繁体   | 混淆字符集                   | 噪声信道模型 , N -gram    |
| [ 38 ], 2014 | 繁体   | 校对规则                    | 图模型 , CRF           |
| [ 39 ], 2014 | 繁体   | 校对词典 , 编辑距离 , 最长匹配分词    | HMM , N -gram , SVM |
| [ 40 ], 2015 | 繁体   | 混淆字符集                   | CRF , N -gram       |
| [ 41 ], 2015 | 繁体   | -                       | N -gram             |
| [ 42 ], 2016 | 简体   | 模式匹配 , 中文串相似度计算         | N -gram             |
| [ 43 ], 2017 | 繁体   | 模式匹配 , E-HowNet , 混淆字符集 | N -gram             |

对于规则和统计相结合的校对方法的研究 , 通常 是改进校对流程的不同阶段的方法 , 可大致分为三类 :

错误识别阶段 基于统计语言模型的检错 。 基 于统计语言模型的检错方法通常都需要先对原句进 行分词 , 然后通过统计语言模型与词性标注序列等 相结合的方式进行检错 , 其中统计语言模型主要用 到 N -gram 等 , 如于勐等人 [23] 提出-种混合校对系 统 HMCTC ( HybridMethodforChineseTextCollation ), 采用最长匹配分词结合词典的方式将原句 分词 , 然后以 Tri-gram 为基础结合语法属性标注进 行检错 , 将相邻词共现频率低于阈值和语法序列标 注不合理的地方标记为错误 ; 张仰森等人 [24] 提出了 -种基于互信息的字词接续判断模型 , 通过判断相 邻字和相邻词的接续性进行检错 。 早期基于统计语

言模型的检错方法通常都需要构建庞大的字字 、 词 词同现频率库 , 这带来了严重的数据稀疏问题 , 造成 这个问题的原因除了统计模型本身的缺陷外 , 还因 为早期的检错方法没有深度地分析中文分词的特 点 。 张仰森等人 [26] 通过分析中文文本的特点指出 , 中文文本大多由二字以上的词构成 , 分词后出现的 连续单字词-般不超过 5 个 , 且出现的单字词多是 助词 、 介词等 , 而含有拼写错误的文本分词后会出现 连续的不合理的单字散串 , 并由此提出了 ' 非多字词 错误 ', 在检错时主要针对分词后出现的连续单字词 进行判断 , 字字同现库通过正确文本中的连续单字 词同现频率进行构建 , 减小了同现频率库的规模 , 缓 解了数据稀疏问题 ; Xie 等人 [41] 对文本中长度等于 2 和大于 2 的连续单字词分别使用 Bi-gram 和

3

索 , 这些模型参数多 、 规模大 、 计算速度慢 , 难以满足 搜索引擎搜索和语音交互等实时场景 。 如何在效果 损失较小的情况下缩小模型规模 、 缩短迭代周期 、 加 快预测速度是-个重要的研究方向 , 如 Sanh 等 人 [105] 提出了 LTD-BERT 模型 ( LearningtoDistill BERT ) 对 BERT 进行了模型压缩 , 在效果损失很小 的基础上 , 降低了存储和运算开销 。

( 4 ) 现阶段中文文本语法错误校对方法主要还 是基于 Seq2Seq 的 NMT 方法 , 通常生成模型需要 大规模的平行语料进行训练 , 而语法纠错相关的语 料则比较匮乏 , 因此如何自动构建大量中文语法校 对训练语料将受到更多学者的关注 。 目前针对语法 校对训练数据不足的问题 , 部分英文语法校对的研 究者提出通过构造伪数据的方法来增加训练数据 , 如 Ge 等人 [107] 将正确语句输入 Seq2Seq , 将错误语 句作为输出 , 训练得到-个错误语句生成模型 ; Lichtarge 等人 [108] 使用翻译系统将英文翻译成-种 中间语言 , 如日语 、 法语等 , 再将中间语言翻译回英 文 , 生成的英语语义和原始英语语句基本保持不变 , 但是往往会存在-些语法错误 。 中文语法校对也可 以参考上述办法构造大规模平行语料 。

( 3 ) 现有的文本自动校对研究主要面向通用领 域 , 随着无纸化办公的普及 , 针对不同领域具体场景 下的文本校对需求迫在眉睫 , 将受到越来越多研究 人员的关注 。 具体应用场景下的文本校对通常需要 在传统校对的基础上进行更加有针对性的建模 , 以 公文领域为例 , 张仰森等人 [106] 指出政治新闻领域 存在的文本错误除常见的拼写 、 语法错误以外 , 还有 领导人顺序错误和领导人姓名 -职务对应错误等 , 针 对政治新闻等领域的文本校对 , 需要分析领域错误 特点 , 单独构建领域词典 。

( 5 ) 语义问题的研究-直是 NLP 研究中的薄弱 环节 , 也是中文文本校对的难点 [95] , 已有的语义错 误校对方法主要是基于规则 、 知识库和语义推理的 方法 [21,96,98] 。 基于规则 、 知识库等的校对方法需要 人工建立规则 , 整理领域词典 , 不适用于大规模的语 义错误校对 , 随着深度学习的不断发展 , 如何通过深 度学习的方法解决语义错误会持续受到学者们的 关注 。

中文文本自动校对作为自然语言处理领域-个 重要研究方向 , -直以来受到相当广泛的关注 。 本 文主要阐述了中文文本拼写错误和语法错误的校对

方法 , 整理了相关共享任务数据集 , 并对未来的研究 方向进行了分析和展望 。

## 参考文献

- [ 1 ] 徐连诚 , 石磊 . 自动文字校对动态规划算法的设计与 实现 [ J ] . 计算机科学 , 2002 , 29 ( 9 ): 149-150.
- [ 3 ] ChoK , VanMerrienboerB , GulcehreC , etal.LearningphraserepresentationsusingRNNencoder-decoder forstatisticalmachinetranslation [ C ]// Proceedingsof theConferenceonEmpiricalMethodsinNaturalLanguageProcessing.Stroudsburg , PA , USA : AssociationforComputationalLinguistics , 2014 : 1724-1734.
- [ 2 ] 龚小谨 , 罗振声 , 骆卫华 . 中文文本自动校对中的语 法错误检查 [ J ] . 计算机工程与应用 , 2003 , 39 ( 8 ): 98-100.
- [ 4 ] SutskeverI , VinyalsO , LeQV.Sequencetosequence learningwithneuralnetworks [ C ]// Proceddingsofthe 27thInternationalConferenceon NeuralInformation ProcessingSystems.Cambridge , USA : MIT Press , 2014 : 3104-3112.
- [ 6 ] LuongT , Pham H , ManningCD.Effectiveapproachesto attention-based neural machine translation [ C ]// Proceedings ofthe Conference on Empirical Methodsin Natural Language Processing.Stroudsburg , PA , USA : AssociationforComputationalLinguistics , 2015 : 1412-1421.
- [ 5 ] BahdanauD , ChoK , BengioY.Neuralmachinetranslationbyjointlylearningtoalignandtranslate [ C ]// Proceedingsof3rdInternationalConferenceonLearningRepresentations.SanDiego , UnitedStates : International Conference on Learning Representations , 2015 : 940-1000.
- [ 7 ] GehringJ , AuliM , GrangierD , etal.Convolutional sequencetosequencelearning [ C ]// Proceedingsofthe 34thInternationalConferenceon Machine Learning. UnitedStates : JMLR , 2017 : 2029-2042.
- [ 9 ] 张仰森 、 丁冰青 . 中文文本自动校对技术现状及展望 [ J ] . 中文信息学报 , 1998 ( 301 ): 51-57.
- [ 8 ] VaswaniA , ShazeerN , ParmarN , etal.Attentionis allyouneed [ C ]// Proceedingsofthe31stInternational ConferenceonNeuralInformationProcessingSystems. RedHook , NY , USA : CurranAssociatesInc , 2017 : 6000-6010.
- [ 10 ] 张仰森 , 俞士汶 . 文本自动校对技术研究综述 [ J ] . 计 算机应用研究 , 2006 , 23 ( 6 ): 8-12.
- [ 11 ] LiuCL , LaiM H , TienK W , etal.Visuallyand phonologicallysimilarcharactersinincorrectChinese words [ J ] .ACMTransactionsonAsianLanguageInformationProcessing , 2011 , 10 ( 2 ): 1-39.