Here's the full content in format ContentFormat.MARKDOWN:

# DocBank: A Benchmark Dataset for Document Layout Analysis

Minghao $\mathrm { I } \mathrm { i } ^ { 1 * } ,$ Yiheng $X u ^ { 2 }$ Lei $\mathrm { C u i } ^ { 2 } ,$ Shaohan Huang2,
Furu Wei2, Zhoujun $\mathrm { L i } ^ { 1 } ,$ Ming Zhou2
1Beihang University
2Microsoft Research Asia
{liminghao1630, lizj}@buaa.edu.cn
{v-yixu, lecu, shaohanh, fuwei, mingzhou}@microsoft.com


## Abstract

Document layout analysis usually relies on computer vision models to understand documents
while ignoring textual information that is vital to capture. Meanwhile, high quality labeled
datasets with both visual and textual information are still insufficient. In this paper, we present
DocBank, a benchmark dataset that contains 500K document pages with fine-grained token-
level annotations for document layout analysis. DocBank is constructed using a simple yet
effective way with weak supervision from the LATEX documents available on the arXiv.com.
With DocBank, models from different modalities can be compared fairly and multi-modal ap-
proaches will be further investigated and boost the performance of document layout analysis.
We build several strong baselines and manually split train/dev/test sets for evaluation. Ex-
periment results show that models trained on DocBank accurately recognize the layout infor-
mation for a variety of documents. The DocBank dataset is publicly available at $h t t p s$ :
//github.com/doc-analysis/DocBank.


## 1 Introduction

Document layout analysis is an important task in many document understanding applications as it can
transform semi-structured information into a structured representation, meanwhile extracting key infor-
mation from the documents. It is a challenging problem due to the varying layouts and formats of the
documents. Existing techniques have been proposed based on conventional rule-based or machine learn-
ing methods, where most of them fail to generalize well because they rely on hand crafted features that
may be not robust to layout variations. Recently, the rapid development of deep learning in computer
vision has significantly boosted the data-driven image-based approaches for document layout analysis.
Although these approaches have been widely adopted and made significant progress, they usually lever-
age visual features while neglecting textual features from the documents. Therefore, it is inevitable to
explore how to leverage the visual and textual information in a unified way for document layout analysis.

Nowadays, the state-of-the-art computer vision and NLP models are often built upon the pre-trained
models (Peters et al., 2018; Radford et al., 2018; Devlin et al., 2018; Lample and Conneau, 2019;
Yang et al., 2019; Dong et al., 2019; Raffel et al., 2019; Xu et al., 2019) followed by fine-tuning on
specific downstream tasks, which achieves very promising results. However, pre-trained models not only
require large-scale unlabeled data for self-supervised learning, but also need high quality labeled data
for task-specific fine-tuning to achieve good performance. For document layout analysis tasks, there
have been some image-based document layout datasets, while most of them are built for computer vision
approaches and they are difficult to apply to NLP methods. In addition, image-based datasets mainly
include the page images and the bounding boxes of large semantic structures, which are not fine-grained
token-level annotations. Moreover, it is also time-consuming and labor-intensive to produce human-
labeled and fine-grained token-level text block arrangement. Therefore, it is vital to leverage weak

Equal contributions during internship at Microsoft Research Asia.

This work is licensed under a Creative Commons Attribution 4.0 International License. License details: http: //
creativecommons.org/licenses/by/4.0/.

<!-- PageNumber="949" -->
<!-- PageFooter="Proceedings of the 28th International Conference on Computational Linguistics, pages 949-960 Barcelona, Spain (Online), December 8-13, 2020" -->
<!-- PageBreak -->


<figure>

MXHAS 000, 1-7 [0000)

Prepeist 23 November 2019

Complied wing MINBAS ISTEX styk file v3.0

Cosmic String Detection with Tree-Based Machine Learning
5

pol f

noise-free

Cosmic String Detection with Tree-Based Machine
Learning

cor

ACT-Ike

M
Planck-like

22

WI

C

lap

A. Vafaei Sadr1,2,3, M. Farhang1, S. M. S. Movahed14 *, B. Bassett3,5,6,7, M. Kunz2
1 Department of Physics, Shahid Beheshti University, Velenjak, Tehran 29838, Aran
a Département de Physique Théorique and Center for Astroparticle Physics, Université de Centre, &4 Quet Ernest Asserment,
teir Centre /. Switzerland

Ms

3 African Institute for Mathersatinal Sciences, 6 Melrose Road, Muizenberg, 7945, South Africa
School of Physics, Istituale for Research in Fundamental Beknees, (930), P. O. Bar 19998-5531, Tehran, Iran
& SKA South Africa, The Park, Park Road, Pinclaude, Cape Town 9105, South Africae
" Department af Metha and Applied Maths, University of Cape Town, Cape Town, South Africa

M4

Cs

der

Ma

23 November 2019

9

ABSTRACT
explore the wee of random forest, and gradient boosting, two powerful tree-based
We EXPLORE Low FRE for the detection of crestuie strings in tungus of the cosmic
microwave background (CMB), through their unique Gott-kader-Sagunto
the temperature anisotropies. The Information in the maps is composed into feature
vectors before being presed to the learning units, The feature wetors contain various
statistical metomures of processed CMB maps that bocet the cosmic string detectability.
Our proposed classifiers, after training, siwn molta improved som er similar to that
chimed detectability levels of the evidence for or the
make It detection of strings with Gp 2 2.1 x 10-10 for pois-free, 09/ resolution CMR.
observations The minisino detectable tension increases to Qu > 3 0% 18-8 for a more

8

WZ

lap

C's

Ca

der

sob

M2

Ma

Figure 5. Feature importance report: the average atmnber of times sach feature neposred among the top boa features, for euch layer of
the pre-processor, for the IF (top) and GB (bottom) korner.

observations. minimum Gu ≥ 3.0x
realistic, CMB S4-like (11) strategy, still a significant improvement over the previous

Table 1. The minimum detectable Gp, ar Gyan, for the two
tree-based algorithmen, GB and RF, and for the five experimental

Tablo 2. Similar to Tablo I but for minimum mesauzable Ga's,

Key words: Cosmic string, Machine learning, Tree hased models, Curveket, CMB,

or Guiums's.

\-

experiment
Guida (GB)
Gpde (RF)

experiment

4.3 × 10-20

2.1 × 10-10

3.6 x 10-5

36 × 10-9
1.2 x

1 INTRODUCTION

The inflationary paradigm is the most widely arrepted
cenario for seeding the structures in the Universe, so far

San Juan tests with flying colors. There is, how-
passmg observat imal beste when y lle bonne mere enn
Habe mos serturistläutet præcist by: cosmic topological de-
Korte farmed at cosmological phase transitions. In particular,
mesle strings (CS) are theoretically expected to be pro-
doved in the oule Universe (Kilde 1976; Zekkovich 1980;

effort has been put into developing powerful statistical tools
Sor ccomic string network detection and putting tight upper
and u represent Newton's constant and the string's tension,
respectively, The string tension is intimately related to the
energy of the phase transition epoch,

Rolse-free
CMB-84-Hơn (11)
x 10-1
CMB-S4-like [I]
2.5 × 10-T
1.2 × 10-7
2.5 × 10-3
1.0 x 10-#
1.0 × 10-8

I

CMB-S4-Tie (11)
CMB-84-like (1)

1.2 x DOCT
1.2 H 10-T
x 1D-T

3.0 x 10 -*
1.2 ×
1.2 x 10-1

ACT-The
Thack-like

2.5 × 10-T

Planck-like
T.O H 10-T
5.0 × 10-7

cial classes, can not make an umbiased measurement of such
small string tensions. For a noise-free observation of the sky.

Shellund 1951; Fincaun det .
Bevis et al. 2018 Creeland et al. 1911: Sakelleriation 1995
Samme & Ty 2003: Copeland et al. 2004: Posteian et al.
2009 Maludar & Christine Dois 2000 Dal & Vileskin
2001; Benry Ter 2009). delection of CS
2004; Kibble 2XH; Henry Tye 3KG). The detection uf Cs
wese (Kibble 1976; Zeldovich 1940) Vilenkin 1981- Vilenkin
& Shellard 2000; Firouzjahi & Tye 2005), Therefore a lot of

where de is the symmetry breaking energy seale, e is the
In this paper we work in natural tits with be - a.
& CS network would leave weioss impeints on cos-
nie siercame backssuend (CMB) abortruedes. The Gutt-
Kaiser-Stebbins (KS) effect (Kabww & Stebbins 1984;
et al. 1997: Pen et al. 1997) Riversnl & Baha sugi
corresponds to the integrated Suchs-Wolfe effect caused by
moving strings. It produces line-like discontinuities on the

Note that Table 2 only reports the malmuita fissasurable
Gel's and not their associated errors. That is because the
uncertainties in our mitvirements are dominated by the bin
sice of Gp classes, soud not the statistical erece. Therefore,
for a clus with Gyil, the mentainty in the measurement
W ouy a dindep & Gpus, imspective of the experiment.
7 DISCUSSION
We proposed a tree-bound machine learning algorithm
for detecting and measuring the trace of CS-Induced signals
CS-induced
Our simulations consisted of 1900 maps, pisood through the
pre-processing unit of the algorithm to form the feature vee-
MNRAS 000, 1-7 (0000)

tors, which are the inputs to the chiesifiers. The simulations
cornequand to 18 chovoxx of Gu in the range Gu = 2.5 x 10-18
to 5 x 1057, with equal spacing in In Gp, and one moll choos
Out of these maps, 90% were werd for training the classifiers
(here takes to be random forest and gradient boosting) and
the rest as test sets. We performed feature analysis on the
Scature vectors to find the significance of the role of euch fa-
ture for the chicoification. The results can be a major help
in reducing the computational eret ce future anabrala hev de
Gebeten the most significant features, As erperal results
co state that the scale of eurvelet components should
be matched to the effective resolution of experiments in the

몰이(국.)

sky,
the algorithm can distinguish the traces of CS networks

(1)

difficult to make a definite recommendation, while the see-
ond moment is the most important statistical measure in
Wer find that, for each experimental case, three Gp

· E-mail: m.a.moxabed&ipm.ir

0000 The Authors

(a)

(b)

(c)

(d)

</figure>


<figure>
<figcaption>Title</figcaption>

Figure 1: Example annotations of the DocBank. The colors of semantic structure labels are: Abstract
Author , Caption , Equation , Figure , Footer , List , Paragraph , Reference , Section
Table
9

</figure>


supervision to obtain fine-grained labeled documents with minimum efforts, meanwhile making the data
be easily applied to any NLP and computer vision approaches.

To this end, we build the DocBank dataset, a document-level benchmark that contains 500K docu-
ment pages with fine-grained token-level annotations for layout analysis. Distinct from the conventional
human-labeled datasets, our approach obtains high quality annotations in a simple yet effective way with
weak supervision. Inspired by existing document layout annotations (Siegel et al., 2018; Li et al., 2019;
Zhong et al., 2019), there are a great number of digital-born documents such as the PDFs of research pa-
pers that are compiled by LATEX using their source code. The LATEX system contains the explicit semantic
structure information using mark-up tags as the building blocks, such as abstract, author, caption, equa-
tion, figure, footer, list, paragraph, reference, section, table and title. To distinguish individual semantic
structures, we manipulate the source code to specify different colors to the text of different semantic
units. In this way, different text zones can be clearly segmented and identified as separate logical roles,
which is shown in Figure 1. The advantage of DocBank is that, it can be used in any sequence labeling
models from the NLP perspective. Meanwhile, DocBank can also be easily converted into image-based
annotations to support object detection models in computer vision. In this way, models from different
modalities can be compared fairly using DocBank, and multi-modal approaches will be further investi-
gated and boost the performance of document layout analysis. To verify the effectiveness of DocBank,
we conduct experiments using four baseline models: 1) BERT (Devlin et al., 2018), a pre-trained model
using only textual information based on the Transformer architecture. 2) RoBERTa (Liu et al., 2019), a
robustly optimized method for pre-training the Transformer architecture. 3) LayoutLM (Xu et al., 2019),
a multi-modal architecture that integrates both the text information and layout information. 4) Faster
R-CNN (Ren et al., 2015), a high performance object detection networks depending on region proposal
algorithms to hypothesize object locations. The experiment results show that the LayoutLM model sig-
nificantly outperforms the BERT and RoBERTa models and the object detection model on DocBank for
document layout analysis. We hope DocBank will empower more document layout analysis models,
meanwhile promoting more customized network structures to make substantial advances in this area.

The contributions of this paper are summarized as follows:

· We present DocBank, a large-scale dataset that is constructed using a weak supervision approach.
It enables models to integrate both the textual and layout information for downstream tasks.

· We conduct a set of experiments with different baseline models and parameter settings, which con-
firms the effectiveness of DocBank for document layout analysis.

· The DocBank dataset is available at https : //github. com/doc-analysis/DocBank.

<!-- PageNumber="950" -->
<!-- PageBreak -->


<figure>
<figcaption>Figure 2: Data processing pipeline</figcaption>

Documents
(.tex)

Semantic structures with
colored fonts
(structure-specific colors)

Token annotations by the
color to structure mapping

</figure>


## 2 Task Definition

The document layout analysis task is to extract the pre-defined semantic units in visually rich documents.
Specifically, given a document $\mathcal{D}$ composed of discrete token set $t = \left\{ t _ { 0 } , t _ { 1 } , \ldots , t _ { n } \right\} ,$ each token $t _ { i } =$
$\left( w , \left( x _ { 0 } , y _ { 0 } , x _ { 1 } , y _ { 1 } \right) \right)$ consists $\mathrm { o f }$ word w and its bounding box $\left( x _ { 0 } , y _ { 0 } , x _ { 1 } , y _ { 1 } \right) .$ And $\mathcal{C} = \left\{ c _ { 0 } , c _ { 1 } , . . , c _ { m } \right\}$
defines the semantic categories that the tokens are classified into. We intend to find a function $F$ :
$\left( \mathcal{C} , \mathcal{D} \right) \rightarrow \mathcal{S} ,$ where $\mathcal{S}$ is the prediction set:

$$\mathcal{S} = \left\{ \left( \left\{ t _ { 0 } ^ { 0 } , \ldots , t _ { 0 } ^ { n _ { 0 } } \right\} , c _ { 0 } \right) , \ldots , \left( \left\{ t _ { k } ^ { 0 } , \ldots , t _ { k } ^ { n _ { k } } \right\} , c _ { k } \right) \right\}$$
(1)


## 3 DocBank

We build DocBank with token-level annotations that supports both NLP and computer vision models.
As shown in Figure 2, the construction of DocBank has three steps: Document Acquisition, Semantic
Structures Detection, Token Annotation. Meanwhile, DocBank can be converted to the format that is
used by computer vision models in a few steps. The current DocBank dataset totally includes 500K
document pages, where the training set includes 400K document pages and both the validation set and
the test set include 50K document pages.


### 3.1 Document Acquisition

We download the PDF files on arXiv.com as well as the LATEX source files since we need to modify
the source code to detect the semantic structures. The papers contain Physics, Mathematics, Computer
Science and many other areas, which is beneficial for the diversity of DocBank to produce robust models.
We focus on English documents in this work and will expand to other languages in the future.


### 3.2 Semantic Structures Detection

DocBank is a natural extension of the TableBank dataset (Li et al., 2019), where other semantic units
are also included for document layout analysis. In this work, the following semantic structures are
annotated in DocBank: {Abstract, Author, Caption, Equation, Figure, Footer, List, Paragraph, Reference,
Section, Table and Title}. In TableBank, the tables are labeled with the help of the 'fcolorbox' command.
However, for DocBank, the target structures are mainly composed of text, where the 'fcolorbox' cannot
be well applied. Therefore, we use the 'color' command to distinguish these semantic structures by
changing their font colors into structure-specific colors. Basically, there are two types of commands to
represent semantic structures. Some of the LATEX commands are simple words preceded by a backslash.
For instance, the section titles in LATEX documents are usually in the format as follows:

\ section {The title of this section}

Other commands often start an environment. For instance, the list declaration in LATEX documents is
shown as follows:

\ begin {itemize }
item First item
\item Second item
\end { itemize }

The command $\backslash b e g i n i t e m i z e$ starts an environment while the command $\backslash e n d i t e m i z e$ ends that
environment. The real command name is declared as the parameters of the 'begin' command and the
'end' command.

<!-- PageNumber="951" -->

