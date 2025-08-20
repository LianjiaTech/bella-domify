# 第36卷 第9期

# 中文信息学报

# Vol.36, No.9

# 2022年9月

# JOURNAL OF CHINESE INFORMATION PROCESSING

# Se.p, 2022

文章编号: 1003-0077202209-0001-18( )

# 中文文本自动校对综述

李云汉1,2, 施运梅1,2, 李宁1,2, 田英爱1,2

(北京信息科技大学 网络文化与数字传播北京市重点实验室, 北京 100101; 1. 北京信息科技大学 计算机学院, 北京 100101)

# 摘 要:

文本校对在新闻发布书刊出版语音输入汉字识别等领域有着极其重要的应用价值，是自然语言处理领域中的一个重要研究方向。该文对中文文本自动校对技术进行了系统性的梳理，将中文文本的错误类型分为拼写错误、语法错误和语义错误，并对这三类错误的校对方法进行了梳理，对中文文本自动校对的数据集和评价方法进行了总结，最后展望了中文文本自动校对技术的未来发展。

# 关键词:

自动校对，拼写错误，语法错误，语义错误，数据集，评估指标;

中图分类号: TP391

文献标识码: A

# ASurveyofAutomaiErrorCorrecionofChnesText

Li Yunhan1,2, Shi Yunmei1,2, Li Ning1,2, Tian Yingai1,2

(1. Beijing Information Science and Technology University Beijing Key Laboratory of Internet Culture Digital Dissemination, Beijing 100101 China; 2. School of Computer, Beijing University of Information Technology, Beijing 100101 China)

# Abstract:

Text correction, an important research field in Natural Language Processing (NLP), is of great application value in fields such as newspaper publication and text input. This paper provides a systematic overview of automatic error correction technology for Chinese texts. Errors in Chinese texts are divided into spelling errors, grammatical errors, and semantic errors, and the methods of error correction for these three types are reviewed. Moreover, datasets and evaluation methods of automatic error correction for Chinese texts are summarized. In the end, prospects for the automatic error correction for Chinese texts are raised.

# Keywords:

automatic correction, spelling errors, grammatical errors, semantic errors, datasets, evaluation indicators;
# 引言

早期中文自动校对方法主要基于统计和规则相结合的方法，采用了分词、统计语言模型、统计机器翻译和混淆字符集等技术。随着深度学习的发展一系列端到端的方法在自然语言处理领域逐渐得到应用，如循环神经网络、序列到序列模型、注意力机制、卷积序列到序列模型和基于自注意力的Transformer模型，中文文本自动校对研究逐渐从基于规则和统计语言模型相结合的方法转向基于深度模型的方法，并且使用序列标注模型、神经机器翻译模型和预训练语言模型进行端到端的校对。

本文概述了中文文本中的常见错误类型，分析了中文文本校对技术的研究发展现状，对中文文本校对共享任务数据集以及校对系统的评估指标进行了归纳总结，最后探讨了中文文本自动校对技术未来发展的方向。

# 1 中文文本的错误类型

中文文本产生的错误可大体分为拼写错误、语法错误和语义错误三类。

# 拼写错误

张仰森等人和Liu等人指出音似、形似字错误是中文文本中常见的拼写错误。形似字错误主要发生在五笔输入和字符识别过程中，音似错误则主要发生在拼音输入和语音识别过程中。其中，音似错误又可以进一步细分为同音同调、同音异调和相似音错误。虽然大部分拼写错误是由音似、形似字误用导致，但也有些错误是由于缺少常识性知识或语言学知识所导致的，如表1所示。

# 语义错误

语义错误是指一些语言错误在字词层面和语法搭配上不存在问题，而是在语义层面上的搭配有误，如表3所示。由于语义错误的处理需要模型理解上下文的语义信息，因此对模型提出了较高的要求，其校对难度要高于拼写错误校对和语法错误校对。

# 表1 常见拼写错误举例

|错误类型|错误|正确|
|---|---|---|
|形似字错误|诞续|延续|
|同音|火势向四周漫(man4)延|火势向四周蔓(man4)延|
|音似|但 是 不 行 (xing2)还 是但 是 不 幸 (xing4)|还是发生了|
|知识型错误|埃及有金子塔|埃及有金字塔|
|推断型错误|越狱在挖洞|为了越狱在挖洞|

# 表2 常见语法错误举例

|错误类型|错误|正确|
|---|---|---|
|字词冗余|我根本不能理解这妇女辞职|我根本不能理解妇女辞职|
|字词缺失|我河边散步的时候。|我在河边散步的时候。|
|搭配不当|还有其他的人也受害。|还有其他的人也受伤害。|
|乱序|世界上每天由于饥饿很多人死亡。|世界上每天很多人由于饥饿死亡。|

# 2 中文文本自动校对方法

中文文本拼写校对流程大致可以分为以下三步：①错误识别：判断文本是否存在拼写错误并标记出错误位置；②生成纠正候选：利用混淆字符或通过模型生成字符等方法构建错误字符的纠正候选；③评估纠正候选：利用某种评分函数或分类器结合局部乃至全局特征对纠正候选排序，排序最高的纠正候选作为最终校对结果。实际上，大部分校对方法的流程都可以划分为上述三步，不过也有部分方法，如基于深度模型端到端的校对方法将错误识别阶段省略，但本质上也属于此流程。

# 2.1 拼写错误校对方法

中文拼写错误校对早期采用的主要是规则和统计语言模型相结合的校对方法，该类方法使用规则和统计语言模型进行检错，在生成候选阶段利用混淆字符或通过模型生成字符等方法构建错误字符的纠正候选。
# 2.. 11 基于规则和统计语言模型结合的校对方法

中文拼写错误校对早期采用的主要是规则和统计语言模型 (Statistical Language Model SLM)相结合的校对方法，该类方法使用规则和统计语言模型进行检错，在生成候选阶段利用混淆字符或通过模型生成字符的方式得到纠正候选字符，最后通过校对词典等，统计语言模型主要使用了N元语法(N-gram)、条件随机场(Conditional Random Fields, CRF)等，如表4所示。

# 表4 基于规则和统计的拼写校对方法

|引用|语言|规则|统计模型|
|---|---|---|---|
|[],1995 22|繁体|混淆字符集|Bi-gram|
|[],1998 23|简体|最长匹配分词|Tri-gram|
|[],2001 24|简体|—|互信息|
|[],2002 25| |混淆字符集,最小编辑距离|Tri-gram,贝叶斯分类器g|
|[],2006 26|简体|非多字词错误查错规则|互信息|
|[],2012 27|繁体|形似字符集|Bi-gram,线性回归g|
|[],2013 28|繁体|混淆字符集|Bi-gram,线性回归g|
|[],2013 29|繁体|混淆字符集,E-HowNet|N-gramg|
|[],2013 30|繁体|混淆字符集,混淆字符替换规则|N-gram|
|[],2013 31|繁体|混淆字符集,校对词典|Tri-gram,CRF|
|[],2013 32|繁体|混淆字符集|N-gram|
|[],2013 33|繁体|—|最大熵|
|[],2013 34|繁体|混淆字符集,词典|SMT,N-gramSVM|
|[],2013 35|繁体|校对词典,检错规则|SMT,N-gram|
|[],2014 36|繁体|混淆字符集|Tri-gram|
|[],2014 37|繁体|混淆字符集|噪声信道模型,N-gramg|
|[],2014 38|繁体|校对规则|图模型,CRF|
|[],2014 39|繁体|校对词典,编辑距离,最长匹配分词|HMM,N-gramSVMg|
|[],2015 40|繁体|混淆字符集|CRF,N-gramg|
|[],2015 41|繁体|—|N-gramg|
|[],2016 42|简体|模式匹配,中文串相似度计算|N-gramg|
|[],2017 43|繁体|模式匹配,E-HowNet,混淆字符集|N-gram|
# 对于规则和统计相结合的校对方法的研究

通常是改进校对流程的不同阶段的方法，可大致分为三类:

# 错误识别阶段

基于统计语言模型的检错。基于统计语言模型的检错方法通常都需要先对原句进行分词，然后通过统计语言模型与词性标注序列等相结合的方式进行检错，其中统计语言模型主要用到N-gram等，如于勐等人提出一种混合校对系统HMCTCHbrid Method for Chinese Text Collation，采用最长匹配分词结合词典的方式将原句分词，然后以Tri-gram为基础结合语法属性标注进行检错，将相邻词共现频率低于阈值和语法序列标注不合理的地方标记为错误; 张仰森等人提出了一种基于互信息的词词接续判断模型，通过判断相邻字和相邻词的接续性进行检错。早期基于统计语言模型的检错方法通常都需要构建庞大的字字、词词同现频率库，这带来了严重的数据稀疏问题，造成这个问题的原因除了统计模型本身的缺陷外，还因为早期的检错方法没有深度地分析中文分词的特点。张仰森等人通过分析中文文本的特点指出，中文文本大多由二字以上的词构成，分词后出现的连续单字词一般不超过5个，且出现的单字词多是助词、介词等，而含有拼写错误的文本分词后会出现连续的不合理的单字散串，并由此提出了非多字词“错误”，在检错时主要针对分词后出现的连续单字词进行判断，字字同现库通过正确文本中的连续单字词同现频率进行构建，减小了同现频率库的规模，缓解了数据稀疏问题; Xie等人对文本中长度等于4和大于2的连续单字词分别使用Bi-ram和g索，这些模型参数多规模大计算速度慢难以满足、方法，整理了相关共享任务数据集并对未来的研究方向进行了分析和展望。

损失较小的情况下缩小模型规模、缩短迭代周期加快预测速度是一个重要的研究方向，如Sanh等人提出了LTD-BERT模型（Learning to Distill BERT）对BERT进行了模型压缩，在效果损失很小的基础上，降低了存储和运算开销。

# 参考文献

1. 徐连诚,石磊.自动文字校对动态规划算法的设计与实现.计算机科学,2002,29(1):149-150.
2. 龚小谨,罗振声,骆卫华.中文文本自动校对中的语法错误检查.计算机工程与应用,2003,39(8):98-100.
3. Cho K, Van Merrienboer B, Gulcehre C et al. Learning phrase representations using RNN encoder-decoder for statistical machine translation. Proceedings of the Conference on Empirical Methods in Natural Language Processing. Stroudsburg, PA, USA: Association for Computational Linguistics, 2014: 1724-1734.
4. Sutskever I, Vinyals O, Le Q V. Sequence to sequence learning with neural networks. Proceedings of the 27th International Conference on Neural Information Processing Systems. Cambridge, USA: MIT Press, 2014: 3104-3112.
5. Bahdanau D, Cho K, Bengio Y. Neural machine translation by jointly learning to align and translate. Proceedings of 3rd International Conference on Learning Representations. San Diego, United States: International Conference on Learning Representations, 2015: 940-1000.
6. Luong T, Pham H, Manning C D. Effective approaches to attention-based neural machine translation. Proceedings of the Conference on Empirical Methods in Natural Language Processing. Stroudsburg, PA, USA: Association for Computational Linguistics, 2015: 412-421.
7. Gehring J, Auli M, Grangier D et al. Convolutional sequence to sequence learning. Proceedings of the 34th International Conference on Machine Learning. United States: JMLR, 2017: 2029-2042.
8. Vaswani A, Shazeer N, Parmar N et al. Attention is all you need. Proceedings of the 31st International Conference on Neural Information Processing Systems. Red Hook, NY, USA: Curran Associates Inc, 2017: 6000-6010.
9. 张仰森、丁冰青.中文文本自动校对技术现状及展望.中文信息学报,1998,30(1):51-57.
10. 张仰森,俞士汶.文本自动校对技术研究综述.计算机应用研究,2006,23(6):8-12.
11. Liu C L, Lai M H, Tien K W, et al. Visual and phonologically similar characters in incorrect Chinese words. ACM Transactions on Asian Language Information Processing, 2011, 10(2): 1-39.