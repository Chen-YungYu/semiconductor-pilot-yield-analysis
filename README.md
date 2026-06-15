# 半導體試產良率分析系統 (Semiconductor Pilot Yield Analysis)

🚀 🖱️ **[點此線上體驗「半導體試產良率分析系統」](https://semiconductor-pilot-yield-analysis-heufbdujzft4xyjdb4zcul.streamlit.app/)**

> **💡 系統載入說明**：本系統採用 Streamlit 雲端部署。若首次開啟遇到系統休眠提示，請點選 **「Yes, get this app back up!」**，系統將於數十秒內完成資源喚醒並載入。

## 📝 專案簡介
本專案專為半導體試產階段（Pilot Run）設計，打造互動分析 Data App。系統將複雜的製程數據進行自動化清洗與統計運算流程；導入 SPC 管制規則進行統計變異監控，結合 Box Plot 與無母數統計檢定科學化評估機台機差，並透過全子集合迴歸模型提供科學化的指標數據，輔助工程師篩選關鍵影響因子並進行決策，大幅縮短異常排查的決策時間。

## ✨ 系統核心分析功能說明 

本系統透過統計學方法，評估機台機差，並協助工程師篩選出對良率具顯著影響的關鍵製程參數： 

### 第一部分：SPC 管制圖監控 (Statistical Process Control) 
- **監控核心**：即時監控各機台的 Yield（良率）與製程參數，檢視其是否皆處於穩定的**隨機變異**狀態。 
- **異常識別**：使用 **3 大管制規則（Rules）**，自動標示並警示製程中可能存在的**系統變異**。 

### 第二部分：箱形圖與機差統計檢定 (Box plot & Statistical Testing) 
- **箱形圖分析 (Box plot)**： 
  - 排除極端值干擾，依數據排序位置識別潛在的 **Outlier（異常值）**。 
  - 直觀呈現各機台的**總變異大小**。 
  - 粗略評估各機台之間是否存在分佈差異。
- **機差顯著性檢定**：
  - 導入 **Kruskal-Wallis Test**，科學化判斷機台間是否存在顯著「機差」。
  - 隨後利用事後檢定 **Dunn's Test**，精準找出是哪一台特定機台發生異常變異，並可與 **Box plot** 的視覺化分佈進行交叉比對驗證。

### 第三部分：多元線性迴歸與特徵篩選 (Correlation & Regression Analysis)
- **線性相關分析**：透過相關係數表，釐清自變數之間、以及各自變數與因變數（良率）之間是否存在線性相關性。
- **OLS 偏迴歸分析**：標示各自變數與因變數之間是否存在顯著性關係。
- **排除共同變異與決策**：交叉比對相關係數與 OLS 顯著性以辨識共同變異。最終使用**全子集合迴歸模型**排除共同變異與發現獨特變異，提供科學化的統計指標，**輔助工程師評估並挑選出預測良率的最佳統計模型**。

## 🛠️ 技術棧 (Tech Stack)
- **程式語言**: Python 3.12
- **網頁框架**: Streamlit
- **核心套件**: NumPy, Pandas, SciPy, Statsmodels, scikit-posthocs, Matplotlib, Plotly 
- **雲端部署**: Streamlit Community Cloud

## 📂 檔案結構說明
- `yield_analyzer_app.py`: 專案核心主程式。實現資料自動化處理與統計的監控和分析，並建構出前端的互動式Data app網頁。
- `requirements.txt`: 版本設定檔案。設定雲端部署（Streamlit Cloud）的版本與開發端完全一致，避免環境差異導致異常。
- `模擬半導體製程良率資料.csv`: 模擬半導體製程數據，用來測試程式邏輯功能。
- `matplotlibrc`: 環境設定檔。解決雲端伺服器（Linux 環境），中文字體無法正常顯示之問題。
- `packages.txt`: Linux 系統套件清單。指定雲端伺服器（Linux 環境）於部署時自動安裝所需的底層中文字型套件，解決圖表亂碼問題。
