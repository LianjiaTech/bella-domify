# 中文文本自动校对综述  

李云汉1,2,施运梅1,2,李 宁1,2,田英爱1,2(1.北京信息科技大学 网络文化与数字传播北京市重点实验室,北京100101;2.北京信息科技大学 计算机学院,北京100101)  

摘 要:文本校对在新闻发布、书刊出版、语音输入、汉字识别等领域有着极其重要的应用价值,是自然语言处理领域中的一个重要研究方向。该文对中文文本自动校对技术进行了系统性的梳理,将中文文本的错误类型分为拼写错误、语法错误和语义错误,并对这三类错误的校对方法进行了梳理,对中文文本自动校对的数据集和评价方法进行了总结,最后展望了中文文本自动校对技术的未来发展。  

关键词:自动校对;拼写错误;语法错误;语义错误;数据集;评估指标中图分类号:TP391 文献标识码:A  

# ASurveyofAutomaticErrorCorrectionofChineseTex  

LiYunhan1,2,ShiYunmei1,2,LiNing1,2,TianYing􀆳ai1,2 (1.BeijingInformationScienceandTechnologyUniversity,BeijingKeyLaboratory ofInternetCultureDigitalDissemination,Beijing100101,China; 2.SchoolofComputer,BeijingUniversityofInformationTechnology,Beijing100101,China)  

Abstract:Textcorrection,animportantresearchfieldin NaturalLanguage Processing (NLP),is ofgreat applicationvalueinfieldssuchasnews,publication,andtextinput.Thispaperprovidesasystematicoverviewof automaticerrorcorrectiontechnologyforChinesetexts.ErrorsinChinesetextsaredividedintospellingerrors, grammaticerrorsandsemanticerrors,andthemethodsoferrorcorrectionforthesethreetypesarereviewed.Moreover,datasetsandevaluationmethodsofautomaticerrorcorrectionforChinesetextsaresummarized.Intheend, prospectsfortheautomaticerrorcorrectionforChinesetextsareraised.  

Keywords:automaticcorrection;spellingerrors;grammaticalerrors;semanticerrors;datasets;evaluationindicators  

# 0 引言  

中文文本自动校对是自然语言处理技术的一个重要应用方面。随着互联网与信息技术的高速发展,中文文本数量呈爆炸式增长,这对传统的手工校对方式提出了严峻挑战。为了降低手工校对工作量,中文文本自动校对相关的研究工作得到了人们的重点关注。中文文本自动校对研究始于 世纪年代,相对于英文文本自动校对研究开始较晚,但其发展速度快且取得了丰硕的研究成果,目前也出现了已经商业化的产品,如黑马校对软件、哈工大讯飞实验室发布的飞鹰智能文本校对系统等。  

早期中文自动校对方法主要基于统计和规则相结合的方法[1-2],采用了分词、统计语言模型、统计机器翻译( , )和混淆字符集等技术。随着深度学习的发展,一系列端到端的方法在自然语言处理(NaturalLanguageProcessing,NLP)领域逐渐得到应用,如循环神经网络(RecurrentNeuralNetwork,RNN)、序列到序列模型(Seuence-to-seuence,Se2se )[3-4]、注意力机制[5-6]、卷积序列到序 列 模 型 (ConvolutionalSequencetoSequence,ConvS2S)[7]和 基 于 自 注 意 力 的 Transformer 模型[8],中文文本自动校对研究逐渐从基于规则和统计语言模型相结合的方法转向基于深度模型的方法,并且使用序列标注模型、神经机器翻译模型(NeuralMachineTranslation,NMT)和预训练语言模型进行端到端的校对。  

本文概述了中文文本中的常见错误类型,分析了中文文本校对技术的研究发展现状,对中文文本校对共享任务数据集以及校对系统的评估指标进行了归纳总结,最后探讨了中文文本自动校对技术未来发展的方向。  

# 1 中文文本的错误类型  

中文文本产生的错误可大体分为拼写错误、语法错误和语义错误三类。  

拼写错误 张仰森等人[9-10]和Liu等人[11]指出音似、形似字错误是中文文本中常见的拼写错误。形似字错误主要发生在五笔输入和字符识别(OticalCharacterReconition,OCR)过程中,音似错误则主要发生在拼音输入和语音识别(AutomatedSpeechRec-onition,ASR)过程中。其中,音似错误又可以进一步细分为同音同调、同音异调和相似音错误[12-13]。虽然大部分拼写错误是由音似、形似字误用导致,但也有些错误是由于缺少常识性知识或语言学知识所导致的,如表1所示。  

表1 常见拼写错误举例  


<html><body><table><tr><td colspan="2">错误类型</td><td>错误</td><td>正确</td></tr><tr><td colspan="2">形似字错误</td><td>诞续</td><td>延续</td></tr><tr><td rowspan="3">音似 字错 误</td><td>同音 同调</td><td>火势向四周漫(man4)延</td><td>火势向四周蔓 (man4)延</td></tr><tr><td>同音 异调</td><td>但是不行（xing2）还是 发生了</td><td>但是不幸（xing4) 还是发生了</td></tr><tr><td>相似 音</td><td>词青(qingl)标注</td><td>词性(xing2)标注</td></tr><tr><td colspan="2">知识型错误</td><td>埃及有金子塔</td><td>埃及有金字塔</td></tr><tr><td colspan="2">推断型错误</td><td>他的求胜欲很强，为了 越狱在挖洞</td><td>他的求生欲很强， 为了越狱在挖洞</td></tr></table></body></html>  

语法错误 NLPTEA 等[14-20]语法错误校对竞赛将中文文本常见语法错误归纳为字词冗余错误(Redundant words,R)、字 词 缺 失 错 误 (Missingwords,M)、搭配不当错误(Selectionerrors,S)和字词乱序错误 (Wordorderingerrors,W),如 表 2所示。  

表2 常见语法错误举例  


<html><body><table><tr><td>错误 类型</td><td>错误</td><td>正确</td></tr><tr><td>字词 冗余</td><td>我根本不能理解这妇女 辞职回家的现象。</td><td>我根本不能理解妇女辞职 回家的现象。</td></tr><tr><td>字词 缺失</td><td>我河边散步的时候。</td><td>我在河边散步的时候。</td></tr><tr><td>搭配 不当</td><td>还有其他的人也受 被害。</td><td>还有其他的人也受伤害。</td></tr><tr><td>字词 乱序</td><td>世界上每天由于饥饿很 多人死亡。</td><td>世界上每天很多人由于饥 饿死亡。</td></tr></table></body></html>  

语义错误 语义错误是指一些语言错误在字词层面和语法搭配上不存在问题,而是在语义层面上的搭配有误[21],如表3所示。由于语义错误的处理需要模型理解上下文的语义信息,因而对模型提出了较高的要求,其校对难度要高于拼写错误校对和语法错误校对。  

表3 常见语义错误举例  


<html><body><table><tr><td>错误类型</td><td>错误</td><td>正确</td></tr><tr><td>知识错误</td><td>中国的首都是南京</td><td>中国的首都是北京</td></tr><tr><td>搭配错误</td><td>他戴着帽子和皮靴就 出门了 出门了</td><td>他戴着帽子穿着皮靴就</td></tr></table></body></html>  

下文中将分别对拼写错误、语法错误和语义错误的自动校对方法进行总结与分析。  

# 2 中文文本自动校对方法  

# 2.1 拼写错误校对方法  

中文文本拼写校对流程大致可以分为以下三步: $\textcircled{1}$ 错误识别:判断文本是否存在拼写错误,并标记出错误位置; $\textcircled{2}$ 生成纠正候选:利用混淆字符或通过模型生成字符等方法构建错误字符的纠正候选; $\textcircled{3}$ 评估纠正候选:利用某种评分函数或分类器等,结合局部乃至全局特征对纠正候选排序,排序最高的纠正候选作为最终校对结果。事实上,大部分校对方法的流程都可以划分为上述三步,不过也有部分方法,如基于深度模型端到端的校对方法,将错误识别阶段省略,但本质上也属于此流程。  

2.1.1 基于规则和统计语言模型结合的校对方法  

中文拼写错误校对早期采用的主要是规则和统计语言模型(StatisticalLanguage Model,SLM)相结合的校对方法,该类方法使用规则和统计语言模型进行检错,在生成候选阶段利用混淆字符或通过模型生成字符的方式得到纠正候选字符,最后通过统计语言模型进行纠正候选的评估,其中,校对规则主要使用了混淆字符集、基于分词的查错规则和校对词典等,统计语言模型主要使用了 $N$ 元语法( $N$ -ram)、条 件 随 机 场 (Conditional Random, )等,如表 所示。  

表4 基于规则和统计的拼写校对方法  


<html><body><table><tr><td>引用</td><td>语言</td><td>规则</td><td>统计模型</td></tr><tr><td>[22],1995</td><td>繁体</td><td>混淆字符集</td><td>Bi-gram</td></tr><tr><td>[23],1998</td><td>简体</td><td>最长匹配分词</td><td>Tri-gram</td></tr><tr><td>[24],2001</td><td>简体</td><td>一</td><td>互信息</td></tr><tr><td>[25],2002</td><td></td><td>混淆字符集,最小编辑距离</td><td>Tri-gram,贝叶斯分类器</td></tr><tr><td>[26],2006</td><td>简体</td><td>非多字词错误查错规则</td><td>互信息</td></tr><tr><td>[27],2012</td><td>繁体</td><td>形似字符集</td><td>Bi-gram,线性回归</td></tr><tr><td>[28],2013</td><td>繁体</td><td>混淆字符集</td><td>Bi-gram,线性回归</td></tr><tr><td>[29],2013</td><td>繁体</td><td>混淆字符集,E-HowNet</td><td>N-gram</td></tr><tr><td>[30],2013</td><td>繁体</td><td>混淆字符集,混淆字符替换规则</td><td>N-gram</td></tr><tr><td>[31],2013</td><td>繁体</td><td>混淆字符集,校对词典</td><td>Tri-gram,CRF</td></tr><tr><td>[32],2013</td><td>繁体</td><td>混淆字符集</td><td>N-gram</td></tr><tr><td>[33],2013</td><td>繁体</td><td>一</td><td>最大熵</td></tr><tr><td>[34],2013</td><td>繁体</td><td>混淆字符集,词典</td><td> SMT,N-gram,SVM</td></tr><tr><td>[35],2013</td><td>繁体</td><td>校对词典,检错规则</td><td>SMT,N-gram</td></tr><tr><td>[36],2014</td><td>繁体</td><td>混淆字符集</td><td>Tri-gram</td></tr><tr><td>[37],2014</td><td>繁体</td><td>混淆字符集</td><td>噪声信道模型,N-gram</td></tr><tr><td>[38],2014</td><td>繁体</td><td>校对规则</td><td>图模型,CRF</td></tr><tr><td>[39],2014</td><td>繁体</td><td>校对词典,编辑距离,最长匹配分词</td><td>HMM, N-gram,SVM</td></tr><tr><td>[40],2015</td><td>繁体</td><td>混淆字符集</td><td>CRF, N-gram</td></tr><tr><td>[41],2015</td><td>繁体</td><td>一</td><td> N-gram </td></tr><tr><td>[42],2016</td><td>简体</td><td>模式匹配,中文串相似度计算</td><td>N-gram </td></tr><tr><td>[43],2017</td><td>繁体</td><td>模式匹配,E-HowNet,混淆字符集</td><td>N-gram</td></tr></table></body></html>  

对于规则和统计相结合的校对方法的研究,通常是改进校对流程的不同阶段的方法,可大致分为三类:  

错误识别阶段 基于统计语言模型的检错。基于统计语言模型的检错方法通常都需要先对原句进行分词,然后通过统计语言模型与词性标注序列等相结合的方式进行检错,其中统计语言模型主要用到 $N$ -ram 等,如于勐等人[23]提出一种混合校对系统 HMCTC(H bridMethodforChineseTextCol-lation),采用最长匹配分词结合词典的方式将原句分词,然后以 为基础结合语法属性标注进行检错,将相邻词共现频率低于阈值和语法序列标注不合理的地方标记为错误;张仰森等人[24]提出了一种基于互信息的字词接续判断模型,通过判断相邻字和相邻词的接续性进行检错。早期基于统计语言模型的检错方法通常都需要构建庞大的字字、词词同现频率库,这带来了严重的数据稀疏问题,造成这个问题的原因除了统计模型本身的缺陷外,还因为早期的检错方法没有深度地分析中文分词的特点。张仰森等人[26]通过分析中文文本的特点指出,中文文本大多由二字以上的词构成,分词后出现的连续单字词一般不超过 个,且出现的单字词多是助词、介词等,而含有拼写错误的文本分词后会出现连续的不合理的单字散串,并由此提出了“非多字词错误”,在检错时主要针对分词后出现的连续单字词进行判断,字字同现库通过正确文本中的连续单字词同现频率进行构建,减小了同现频率库的规模,缓解了数据稀疏问题;Xie等人[41]对文本中长度等于2和大于 2 的连续单字词分别使用 Bi-ram 和索,这些模型参数多、规模大、计算速度慢,难以满足搜索引擎搜索和语音交互等实时场景。如何在效果损失较小的情况下缩小模型规模、缩短迭代周期、加快预测速度是一个重要的研究方向,如 等人[105]提出了 LTD-BERT 模型(LearningtoDistill)对 进行了模型压缩,在效果损失很小的基础上,降低了存储和运算开销。  

(3)现有的文本自动校对研究主要面向通用领域,随着无纸化办公的普及,针对不同领域具体场景下的文本校对需求迫在眉睫,将受到越来越多研究人员的关注。具体应用场景下的文本校对通常需要在传统校对的基础上进行更加有针对性的建模,以公文领域为例,张仰森等人[106]指出政治新闻领域存在的文本错误除常见的拼写、语法错误以外,还有领导人顺序错误和领导人姓名-职务对应错误等,针对政治新闻等领域的文本校对,需要分析领域错误特点,单独构建领域词典。  

(4)现阶段中文文本语法错误校对方法主要还是基于Seq2Seq的 NMT 方法,通常生成模型需要大规模的平行语料进行训练,而语法纠错相关的语料则比较匮乏,因此如何自动构建大量中文语法校对训练语料将受到更多学者的关注。目前针对语法校对训练数据不足的问题,部分英文语法校对的研究者提出通过构造伪数据的方法来增加训练数据,如Ge等人[107]将正确语句输入Seq2Seq,将错误语句作为输出,训练得到一个错误语句生成模型;Lichtarge等人[108]使用翻译系统将英文翻译成一种中间语言,如日语、法语等,再将中间语言翻译回英文,生成的英语语义和原始英语语句基本保持不变,但是往往会存在一些语法错误。中文语法校对也可以参考上述办法构造大规模平行语料。  

(5)语义问题的研究一直是NLP研究中的薄弱环节,也是中文文本校对的难点[95],已有的语义错误校对方法主要是基于规则、知识库和语义推理的方法[21,96,98]。基于规则、知识库等的校对方法需要人工建立规则,整理领域词典,不适用于大规模的语义错误校对,随着深度学习的不断发展,如何通过深度学习的方法解决语义错误会持续受到学者们的关注。  

中文文本自动校对作为自然语言处理领域一个重要研究方向,一直以来受到相当广泛的关注。本文主要阐述了中文文本拼写错误和语法错误的校对方法,整理了相关共享任务数据集,并对未来的研究方向进行了分析和展望。  

# 参考文献  

[1] 徐连诚,石磊.自动文字校对动态规划算法的设计与 实现[J].计算机科学,2002,29(9):149-150.   
[2] 龚小谨,罗振声,骆卫华.中文文本自动校对中的语 法错误检查[J].计算机工程与应用,2003,39(8): 98-100.   
[3] ChoK,VanMerrienboerB,GulcehreC,etal.LearningphraserepresentationsusingRNNencoder-decoder forstatisticalmachinetranslation[C]//Proceedingsof theConferenceonEmpiricalMethodsinNaturalLanguageProcessing.Stroudsburg,PA,USA:AssociationforComputationalLinguistics,2014:1724-1734.   
[4] SutskeverI,VinyalsO,LeQV.Sequencetosequence learningwithneuralnetworks[C]//Proceddingsofthe 27thInternationalConferenceon NeuralInformation ProcessingSystems.Cambridge,USA:MIT Press, 2014:3104-3112.   
[5] BahdanauD,ChoK,BengioY.Neuralmachinetranslationbyjointlylearningtoalignandtranslate[C]// Proceedingsof3rdInternationalConferenceonLearningRepresentations.SanDiego,UnitedStates:International Conference on Learning Representations, 2015:940-1000.   
[6] LuongT,Pham H,ManningC D.Effectiveapproaches to attention-based neural machine translation [C]//Proceedings ofthe Conference on Empirical Methodsin Natural Language Processing.Stroudsburg,PA,USA:AssociationforComputationalLinguistics,2015:1412-1421.   
[7] GehringJ,AuliM,GrangierD,etal.Convolutional sequencetosequencelearning[C]//Proceedingsofthe 34thInternationalConferenceon Machine Learning. UnitedStates:JMLR,2017:2029-2042.   
[8] VaswaniA,ShazeerN,ParmarN,etal.Attentionis allyouneed[C]//Proceedingsofthe31stInternational ConferenceonNeuralInformationProcessingSystems. RedHook,NY,USA:CurranAssociatesInc,2017: 6000-6010.   
[9] 张仰森、丁冰青.中文文本自动校对技术现状及展望 [J].中文信息学报,1998(301):51-57.   
[10] 张仰森,俞士汶.文本自动校对技术研究综述[J].计 算机应用研究,2006,23(6):8-12.   
[11] LiuCL,LaiM H,TienK W,etal.Visuallyand phonologicallysimilarcharactersinincorrectChinese words[J].ACM TransactionsonAsianLanguageInformationProcessing,2011,10(2):1-39.  