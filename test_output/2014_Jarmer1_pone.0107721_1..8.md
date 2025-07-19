---
title: pone.0107721 1..8
authors:
- Karin Wolffhechel1*, Jens Fagertun2, Ulrik Plesner Jacobsen1, Wiktor Majewski1,
  Astrid, Sofie Hemmingsen3, Catrine Lohmann Larsen3, Sofie Katrine Lorentzen3, Hanne
  Jarmer1
year: '2014'
doi: 10.1371/journal.pone.0107721
tags:
- academic
- japanese
- research-paper
- year-2014
created: '2025-07-19'
pdf-path: '[[Wolffhechel et al. 2014 - Interpretation of appearance - the effect of
  facial features on first impressions and personality.PDF]]'
abstract-by: gemini-2.0-flash-001
language: ja
page-count: 8
file-size-mb: 1.92
---

# pone.0107721 1..8

## 🧪 各実験の詳細

### 実験 1
**目的と仮説**: 自己申告による性格特性と、他者による顔の評価（第一印象）との間に相関関係があるかどうかを検証する。 * **実験手法**
**実験参加者**: デンマーク工科大学の学生と職員244名（女性128名、男性116名、平均年齢24.56歳、年齢範囲18-37歳）。 の顔写真を撮影。参加者は、他の20名の参加者の顔写真について、12の特性（友好的、冒険好き、短気、健康的、外向的、支配的、魅力的、男性的、精神的に安定、責任感がある、知的）を9段階のリカート尺度で評価。また、参加者はCIPQ 2.0（Cubiks In-depth Personality Questionnaire）という自己申告式の性格検査を受け、Big Five（ビッグファイブ）を含む17の性格特性を測定。 は約20人の他の参加者によって評価され、各質問に対するスコアの平均が、その参加者の実際のスコアとして使用された。Cronbach's alphaを計算し、このアプローチの信頼性を確認。 の性格特性のスコアと各性別の評価との関連性を明らかにするために、ピアソンの相関係数（Pearson Correlation Coefficient, r）を計算。相関の有意性は、10,000回の繰り返しによる順列検定（permutation test）によって確認。
**課題と刺激**: 各参加者の顔写真を撮影。参加者は、他の20名の参加者の顔写真について、12の特性（友好的、冒険好き、短気、健康的、外向的、支配的、魅力的、男性的、精神的に安定、責任感がある、知的）を9段階のリカート尺度で評価。また、参加者はCIPQ 2.0（Cubiks In-depth Personality Questionnaire）という自己申告式の性格検査を受け、Big Five（ビッグファイブ）を含む17の性格特性を測定。
**手続き**: 各参加者は約20人の他の参加者によって評価され、各質問に対するスコアの平均が、その参加者の実際のスコアとして使用された。Cronbach's alphaを計算し、このアプローチの信頼性を確認。
**分析方法**: 参加者の性格特性のスコアと各性別の評価との関連性を明らかにするために、ピアソンの相関係数（Pearson Correlation Coefficient, r）を計算。相関の有意性は、10,000回の繰り返しによる順列検定（permutation test）によって確認。
**結果と小括**: * 平均評価スコアを用いた場合、男性では責任感と信頼性、女性では精神的な安定性と努力との間に有意な相関が見られた。しかし、個々の評価者のスコアを用いた場合、これらの相関は統計的に有意ではなかった。 * 評価は、支配性-男らしさ、魅力-健康-外向性、信頼性-友好的さの3つのクラスターに分類された。 * 女性は一般的に信頼でき、責任感があり、魅力的であると認識され、男性は精神的に安定していると認識された。

### 実験 2
**目的と仮説**: 顔の特徴から性格特性や第一印象を予測できるかどうかを検証する。 * **実験手法**

### 実験 1
**実験参加者**: 実験1と同じ。
**課題と刺激**: 顔の形状とテクスチャの情報をモデル化するAppearance Model (AM)を作成。顔写真から顔のランドマークの位置とサイズをアノテーションし、主成分分析（Principal Component Analysis, PCA）によって顔の形状のバリエーションを抽出。同様に、テクスチャ情報もPCAによってモデル化。
**手続き**: 顔の特徴を予測変数として、第一印象（Ratings）と性格特性を予測するモデルを構築。線形回帰モデル、サポートベクターマシン、ニューラルネットワークなど、様々なモデルを試した。モデルの性能は、20分割交差検証（20-fold cross-validation）を行い、Pearsonの相関係数（r）を用いて評価。
**分析方法**: , PCA）によって顔の形状のバリエーションを抽出。同様に、テクスチャ情報もPCAによってモデル化。
**結果と小括**: * 性格特性を予測することはできなかったが、顔の特徴から第一印象を予測することはある程度可能であった。男性に対する友好的さの評価が最も高い精度で予測できた（r = .65）。 * 線形回帰モデルが最も正確であり、より複雑なモデルでは予測精度は向上しなかった。

### 実験 3
**目的と仮説**: 特定の性格特性を強く表現する顔を人工的に生成し、それが実際にその特性を表現していると認識されるかを検証する。 * **実験手法**
**実験参加者**: 最初のコホートには参加していない116名。
**課題と刺激**: 線形回帰モデルの係数を使用して、各性別および各評価について2つの極端な顔（高スコアと低スコアの顔）を生成。これらの顔は、顔の特徴の正または負の方向に4標準偏差を適用することによって作成。
**手続き**: 116名の参加者に対し、4つの顔の中から特定の性格特性を最もよく表している顔を選ばせる。4つの顔のうち1つは、特定の評価に対する極端な顔であり、他の3つは同じパラメータ空間からランダムに生成された。
**分析方法**: 各顔が選択された割合を計算し、ランダム選択と比較。
**結果と小括**: * 男性の場合、すべての特性において、極端な顔がランダムな顔よりも有意に多く選択された。女性の場合、友好的さと冒険好きさの特性においてのみ、有意な差が見られた。

## 💡 総合考察と結論

. 総合考察と結論 (General Discussion) 結果の統合: 顔の特徴から性格特性を予測することはできなかったが、第一印象を予測することは可能であった。また、顔の特徴と第一印象の間に有意な関連性があることが確認された。 結論: 顔の特徴は第一印象に影響を与え、人々は顔に基づいて性格のいくつかの側面を評価することに概ね同意する。しかし、これらの評価は自己測定された性格特性とはかけ離れていることが多い。 学術的貢献: 本研究は、顔の特徴が第一印象に与える影響を確認し、顔評価には3つの要因（支配性-男らしさ、信頼性-友好的さ、魅力-健康-外向性）で十分であることを再現した。 研究の限界と今後の展望: 単一の顔写真では、多様な特性を評価するための情報が不足している可能性がある。今後は、動画などを用いて、より完全な第一印象を収集することが望ましい。

## 📈 図表

- **Figure 1**: Data processing (p.2)
- **Figure 1**: Example of two facial features, PC2 and PC13, and (p.2)
- **Figure 2**: ), (p.3)
- **Figure 3**: ). For men the most significant link was (p.3)
- **Figure 4**: visualises the correlation between observed (p.3)
- **Figure 5**: and all (p.3)
- **Figure 4**: B). The male extreme faces for Dominating (Figure 4C) (p.3)
- **Figure 4**: D) (p.3)
- **Figure 6**: we (p.4)
- **Figure 2**: Network graph of all significant correlations between Ratings. The network depicts the relationship between the individual Ratings (p.4)

## 🔗 関連ノート

*[app-obsidian_ai_organizerで自動追加]*

## 📚 参考文献（抜粋）

1. [20]. To visualise the models we generated artificial faces predicted to express a given trait either to a high or a low degree. Three pairs of these extreme faces for each gender are shown in Figure 5 and all face pairs are shown in Figures S2 and S3. Our model is built from holistic features and therefore it is difficult to conclusively state much about specific parts of a face, but some differences stand out in the extreme pairs. For appearing friendly the mouth seems to have an impact: a wider mouth with neutrally or upwards pointed corners of the lips resulted in higher scores for friendliness (Figure 4B). The male extreme faces for Dominating (Figure 4C) reveal the effect of a wider face and a more pronounced eyebrow- ridge. For women the extreme faces for Adventurous (Figure 4D) indicate a positive impact of fuller lips and dark lashes (possibly eye make-up). We performed a validation of our extreme faces by asking 116 people outside the original study to choose between four artificial faces the one that looked to posses a certain personality trait to the The Effect of Facial Features on First Impressions and Personality PLOS ONE | www.plosone.org 3 September 2014 | Volume 9 | Issue 9 | e107721
2. 0.92) than for the female faces (0.63,a,0.87). We used the average score for each Rating as a more reliable measure, based on responses from multiple people, for how a face is assessed by others. The Ratings were seen to fall into three clusters (Figure 2), which we named dominance-masculinity, attractiveness-health- extraversion, and trustworthiness-friendliness. The attractiveness cluster seemingly represents the halo effect (the hypothesis stating that attractive people are evaluated more positively regarding positively loaded personality traits [28,29]): High scores for Attractive clustered with high scores for Extraverted, Emotionally Stable, Physically Healthy, and Adventurous. We further discov- ered a clear link between scores for Dominating and Masculine for men (r(114) = .73, p,.001), which was in agreement with previous results [14,30]. We compared the Ratings between genders with a Welsh’s t-test and found that women generally are perceived as more trustworthy (p = 3.1961025), responsible (p = 4.40610210) and attractive (p = 6.3561029), whereas men are seen as more emotionally stable (p = 4.0461026). Connecting the participants’ personality-trait scores to the Ratings for each gender revealed subtle, but significant correla- tions (.20# abs(r) $.32, p,.01), which did not overlap between genders (see Figure 3). For men the most significant link was between evaluations for Responsible and the personality trait Trusting, a sub-trait of Agreeableness (r(116) = .27). Additionally we found a tendency that men with a more calm personality appear more friendly and extraverted (r(116) = .20). For women the strongest link was between the evaluations for Emotionally Stable and the personality trait Striving, a sub-trait of Conscien- tiousness (r(128) = .32). Dominance was also for women linked to higher scores in the corresponding personality trait Shaping (r(128) = .23, p,.01). Higher scores for Openness to Experience followed higher evaluations for many Ratings including the traits Adventurous (r(128) = .28) and Friendly (r(128) = .27). We found no connection between participants self-reported personality traits and the scores they gave others in the Ratings. Since effect sizes from correlated average scores can be inflated [31,32], we also correlated the raw scores given by each individual judge with the personality scores and then calculated averages and standard deviations for all these correlations based on individual judges. This resulted in effect sizes dropping below statistical significance (see Figure S1) with large standard deviations (.31, s,.39) revealing a substantial individual factor in trait evalua- tions. Since it was our goal to investigate subtle effects of facial features on trait evaluations and we wanted a more complete measure of the trait evaluations we continued with the averaged scores, but the above found group-based effect sizes should be noted as inflated on the individual level. Next, we explored the possibility of predicting single personality traits either from a person’s Ratings or from his or her facial features. However, diverse non-linear approaches and varying subsets of predictors could not predict the personality traits, revealing the correlations as not strong enough for a stable prediction. The performance, when comparing the predicted and the observed personality traits, was low (r,.20, RMSE.2.00) and residual plots showed no satisfying fit. The prediction of a person’s Ratings from his or her facial features, however, gave more reliable results: it is to a certain extent possible to predict how a given person will be perceived based on his or her facial characteristics. We found a linear regression model to be most accurate, whereas more complex models (e.g. support vector machines with linear and radial kernels and a neural network with varying numbers of hidden nodes) did not improve the prediction significantly. The scores for Friendly for men were predicted with the highest accuracy (r = .65, s = 0.04). Figure 4 visualises the correlation between observed and predicted scores for all Ratings for both genders with the corresponding Cronbach’s a We observed predictions being overall better for male faces (p,.001), which is in agreement with the higher values of Cronbach’s a for these. The correlation between the Cronbach’s a and the prediction accuracy was substantial (r = .51, p,.02), again confirming the importance of the agreement between raters for the validity of a given prediction
3. 16. Zebrowitz LA, Kikuchi M, Fellous JM (2010) Facial Resemblance to Emotions: Group Differences, Impression Effects, and Race Stereotypes. Journal of Personality and Social Psychology 98: 175–189. The Effect of Facial Features on First Impressions and Personality PLOS ONE | www.plosone.org 7 September 2014 | Volume 9 | Issue 9 | e107721
4. 15. Zebrowitz LA, Montepare JM (2008) Social Psychological Face Perception: Why Appearance Matters. Soc Personal Psychol Compass 2: 1497–1517.
5. 1143.

*... and 14 more references*

## 📝 個人的なメモ

- [ ] 詳細を読む
- [ ] 実装を試す
- [ ] 関連研究を調査