# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import pandas as pd
import numpy as np
import scipy.stats as stats
import scikit_posthocs as sp   #事後檢定用
import matplotlib.pyplot as plt
import streamlit as st


from statsmodels.formula.api import ols	
import statsmodels.stats.anova as anova 
import itertools 

import plotly.graph_objects as go  #要增加圖片的互動體驗
#import plotly.io as pio  #設定互動圖片在網頁打開，程式設計除錯用
#pio.renderers.default = 'browser'
  

#解決圖片亂碼問題，Windows使用微軟正黑體、Linux系統使用思源黑體
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'Noto Sans CJK TC', 'DejaVu Sans']  
plt.rcParams['axes.unicode_minus'] = False


#讀取模擬半導體機台製程良率資料.csv，設定index為LotID
process_raw_data=pd.read_csv('模擬半導體製程良率資料.csv',sep=',',index_col='LotID')

#依機台，設定分組規則
groups=process_raw_data.groupby("Machine") 

#找出所有機台名稱 
all_m_name=list(process_raw_data["Machine"].unique())  

#找出所有自變數
all_x=[i for i in list(process_raw_data.columns) if i not in ["Machine","Defect","Output","Yield" ]]
  
#設定因變數
rv="Yield"

#切換圖表繪圖後端用，有"Matplotlib" 與 "Plotly"
set_plot_backend="Plotly"


#網頁主題設定
st.set_page_config(page_title="半導體製程Pilot Run Test",layout="wide")


#=======================控制面板========================
with st.sidebar:    
    st.title("⚙️控制面板")
    
    #Yield I-MR Chart控制功能
    st.subheader("I-MR Chart 控制功能")
    st.write("SPC Rule")
    rule1_chk=st.checkbox("OOC")
    rule2_chk=st.checkbox("連續六點向上(向下)")
    rule3_chk=st.checkbox("連續九點在單邊")
    
    #製程參數 I-MR Chart控制功能
    selected_rv=st.selectbox("請選擇一個監控的製程參數",options=all_x)
           


#=======================資料處理========================        
   
#I_MR版的SPC類別物件，用來產生I-MR Chart
class I_mr_chart():
    """
    1.可產生I-MR Chart實例，內整併一個機台的資料
    2.物件具有監控ooc_rule、six_point_trend_rule和night_point_rule的三個方法
    3.例的屬性fig_i_mr_chart可以產生I-MR Char圖表
    4.d2防偏因子，設定組內數目為2 
    5.具有圖表繪圖後端切換功能，可使用物件參數切換"Matplotlib"或"Plotly"，以提升使用者互動性
    """
    def __init__(self,groups,selected_m_name,rv,set_plot_backend):       
        d2=1.128  #d2防偏因子，設定組內數目為2    
        
        self.groups=groups    
        self.selected_m_name=selected_m_name  
        self.rv=rv      
        self.set_plot_backend=set_plot_backend   #圖表繪圖後端切換功能
                
        #計算CL
        m_yield_mean=groups[rv].mean()
        cl=m_yield_mean.loc[selected_m_name]
     
        #計算MR_bar
        mr_i=pd.DataFrame({"i+1項":groups.get_group(selected_m_name)[self.rv].shift(-1),
                           "第i項":groups.get_group(selected_m_name)[self.rv]}
                          )
        mr_i["第i+1項-第i項"]=abs(mr_i["i+1項"]-mr_i["第i項"])      
        mr_bar=(mr_i.dropna(axis=0)["第i+1項-第i項"].sum())/(len(mr_i.dropna(axis=0).index))
       
        #計算UCL
        self.ucl=cl+(3/d2)*mr_bar
        if self.rv=="Yield" and self.ucl>100:     #Yield超過100的值，無意義
            self.ucl=100
        else:
            pass
    
        #計算LCL
        self.lcl=cl-(3/d2)*mr_bar    
        if self.rv=="Yield" and self.lcl<0:       #Yield低於0的值，無意義
            self.lcl=0
        else:
            pass
    
        #畫出I-MR Chart 
        self.i_mr_chart_data=pd.DataFrame({self.rv:groups.get_group(self.selected_m_name)[self.rv],
                                           "UCL":self.ucl,
                                           "CL":cl,
                                           "LCL":self.lcl}
                                          )         #將畫I-MR Chart需要的資料整理成df     
       
        if  self.set_plot_backend=="Matplotlib":       #切換圖表繪圖後端的功能
            self.fig_i_mr_chart,self.ax=plt.subplots()
            self.ax.set_title(f"Machine {self.selected_m_name} {self.rv} ： I-MR Chart")     #標題設定
            
            self.ax.plot(self.i_mr_chart_data[self.rv], label=self.rv, color="blue",marker="s")   #顏色:標準藍
            self.ax.plot(self.i_mr_chart_data["UCL"], label="UCL", color="#F57C00",linestyle="--")      #顏色：中度亮橘色
            self.ax.plot(self.i_mr_chart_data["CL"], label="CL", color="#16A34A")        #顏色：活力正綠色
            self.ax.plot(self.i_mr_chart_data["LCL"], label="LCL", color="#F57C00",linestyle="--")      #顏色：中度亮橘色
            self.ax.tick_params(axis="x",labelrotation=-90)     #X軸標籤順時鐘轉90度
            
            self.ax.legend(fontsize="small",loc="best")  #顯示圖例 
        
        else:   #圖表繪圖後端設定為Plotly
            self.fig_i_mr_chart=go.Figure()
            self.fig_i_mr_chart.update_layout(template="plotly_dark") #圖片主題設定
            self.fig_i_mr_chart.update_layout(margin=dict(t=30,b=10,l=10,r=10)) #調整繪圖區大小
            self.fig_i_mr_chart.update_layout(xaxis=dict(showline=True,mirror=True,linewidth=1,linecolor="#808080"), #繪圖區邊框，顏色：正灰色
                                              yaxis=dict(showline=True,mirror=True,linewidth=1,linecolor="#808080"),
                                              )
            self.fig_i_mr_chart.update_layout(xaxis=dict(ticks="outside",tickwidth=1,tickcolor="#808080"), #設定刻度線，顏色：正灰色
                                              yaxis=dict(ticks="outside",tickwidth=1,tickcolor="#808080")
                                              )  
            self.fig_i_mr_chart.update_layout(title=dict(text=f"Machine {self.selected_m_name} {self.rv} ： I-MR Chart",x=0.5,y=1.0,xanchor="center",yanchor="top",pad=dict(t=0,b=0,l=0,r=0))) #標題設定
            self.fig_i_mr_chart.update_layout(legend=dict(orientation="h",xanchor="left",x=0,y=-0.15,font=dict(size=9),itemwidth=30,tracegroupgap=0)) #設定圖例
            self.fig_i_mr_chart.update_layout(font=dict(family="Microsoft JhengHei")) #設定字型
            
            
            
            self.fig_i_mr_chart.add_scatter(x=self.i_mr_chart_data.index,y=self.i_mr_chart_data[self.rv],mode='lines+markers',name=self.rv,line=dict(color="#3B82F6",dash="solid"),marker=dict(size=9,symbol="square"))  #顏色:標準藍
            self.fig_i_mr_chart.add_scatter(x=self.i_mr_chart_data.index,y=self.i_mr_chart_data["UCL"],mode='lines',name="UCL",line=dict(color="#F57C00",dash="dash"))   #顏色：中度亮橘色
            self.fig_i_mr_chart.add_scatter(x=self.i_mr_chart_data.index,y=self.i_mr_chart_data["CL"],mode='lines',name="CL",line=dict(color="#16A34A",dash="solid"))     #顏色：活力正綠色
            self.fig_i_mr_chart.add_scatter(x=self.i_mr_chart_data.index,y=self.i_mr_chart_data["LCL"],mode='lines',name="LCL",line=dict(color="#F57C00",dash="dash"))  #顏色：中度亮橘色
            
            self.fig_i_mr_chart.update_xaxes(tickangle=90)  #X軸標籤順時鐘轉90度
            
                       
        #制作一個OOC的DataFrame表單作為實例的屬性，供下面三個方法使用
        self.ooc=self.i_mr_chart_data.copy()      

    #檢查是否有Out of Control limit的點，並在圖表標上紅色
    def ooc_rule(self):
        """
        1.檢查是否有Out of Control limit的點，並在圖表標上紅色 
        2.具有圖表繪圖後端切換功能
        """
        
        normal_condition=(self.ooc[self.rv]<=self.ucl) & (self.ooc[self.rv]>=self.lcl)  #control limit內的規則
        self.ooc.loc[:,"OOC"]=self.ooc.loc[:,self.rv]
        self.ooc.loc[normal_condition,"OOC"]=np.nan  #滿足control limit的點其值改成nan
        
        if  self.set_plot_backend=="Matplotlib":       #切換圖表繪圖後端
            self.ax.plot(self.ooc["OOC"],label="OOC",linestyle="",color="#EF4444",marker="s")  #標上OOC點，顏色：警示紅
            
            self.ax.legend(fontsize="small",loc="best")  #顯示圖例 
            
        else:   #圖表繪圖後端設定為Plotly
            self.fig_i_mr_chart.add_scatter(x=self.ooc.index,y=self.ooc["OOC"],mode='markers',name="OOC",marker=dict(size=9,color="#EF4444",symbol="square"))  #顏色：警示紅
                
        return None
        
    #檢查是否有連續六點上升(下降)，並在圖表標上紅色(所有點都標)
    def six_point_trend_rule(self):    
        """
        1.檢查是否有連續六點上升(下降)，並在圖表標上紅色(所有點都標)
        2.具有圖表繪圖後端切換功能
        """
        self.ooc["第i項-第i-1項"]=self.ooc[self.rv]-self.ooc[self.rv].shift(1)     #檢查區間是否有連續上升(下降)用
        for x in ["六點上升","六點下降"]:
            if x=="六點上升":    
                temp=self.ooc["第i項-第i-1項"]>0  #判斷那些區間是上升
            else:
                temp=self.ooc["第i項-第i-1項"]<0  #判斷那些區間是下降
                
            temp=temp.rolling(5).sum()==5  #連續6點上升(下降)往回看，間隔會上升(下降)5次，標第6個上升(下降)點
            temp[temp==False]=np.nan     #正常的點改成nan
            temp=temp.bfill(limit=5)     #第6個上升(下降)點前的5個點也標示 
            temp.loc[temp==True]=self.ooc.loc[temp==True,self.rv]    #將異常點的Yield填入
            self.ooc[x]=temp     #將第6個上升(下降)點納入OOC表單
            
            if  self.set_plot_backend=="Matplotlib":       #切換圖表繪圖後端
                if x!="六點下降":    #只讓圖例只顯示一個
                    self.ax.plot(self.ooc[x],linestyle="",color="#95A5A6",marker="s")  #標上連續六點上升(下降)的點，不顯示圖例，顏色：混泥土色
                else:
                    self.ax.plot(self.ooc[x],label="6pts Trend",linestyle="",color="#95A5A6",marker="s")  #標上連續六點上升(下降)的點，顏色：混泥土色
                
                self.ax.legend(fontsize="small",loc="best")  #顯示圖例
                
            else: #圖表繪圖後端設定為Plotly
                if x!="六點下降":    #只讓圖例只顯示一個
                    self.fig_i_mr_chart.add_scatter(x=self.ooc.index,y=self.ooc[x],mode='markers',name="6pts Trend",marker=dict(size=9,color="#95A5A6",symbol="square"),showlegend=False) #標上連續六點上升(下降)的點，不顯示圖例，顏色：混泥土色
                else:
                    self.fig_i_mr_chart.add_scatter(x=self.ooc.index,y=self.ooc[x],mode='markers',name="6pts Trend",marker=dict(size=9,color="#95A5A6",symbol="square"))  #標上連續六點上升(下降)的點，顏色：混泥土色
                
        return None
    
    #檢查是否有連續9點在上邊(下邊)，並在圖表標上紅色(所有點都標)
    def night_point_rule(self):
        """
        1.檢查是否有連續9點在上邊(下邊)，並在圖表標上紅色(所有點都標)
        2.具有圖表繪圖後端切換功能
        """
        self.ooc["第i項-CL"]=self.ooc[self.rv]-self.ooc["CL"]    #確認是否在單邊用，正數為上邊，負數為下邊連續上升(下降)用
        for x in ["連續9點在上邊","連續9點在下邊"]:
            if x=="連續9點在上邊":
                temp=self.ooc["第i項-CL"]>0 #判斷那些點在上邊
            else:
                temp=self.ooc["第i項-CL"]<0  #判斷那些點在下邊
                
            temp=temp.rolling(9).sum()==9  #連續9點在上邊(下邊)往回看，會有連續9個點為正數(負數)，標第9個點
            temp[temp==False]=np.nan     #正常的點改成nan
            temp=temp.bfill(limit=8)     #第9個點前的8個點也標示 
            temp.loc[temp==True]=self.ooc.loc[temp==True,self.rv]    #將異常點的Yield填入
            self.ooc[x]=temp    #將連續9點在上邊(下邊)的點納入OOC表單
            
            if  self.set_plot_backend=="Matplotlib":       #切換圖表繪圖後端            
                if x!="連續9點在下邊":    #圖例只顯示一個
                    self.ax.plot(self.ooc[x],linestyle="",color="#EF4444",marker=".")  #標上連續9點在上邊(下邊)的點，顏色：警示紅
                else:    
                    self.ax.plot(self.ooc[x],label="9pts One-side",linestyle="",color="#EF4444",marker=".")  #標上連續9點在上邊(下邊)的點，顏色：警示紅
                
                self.ax.legend(fontsize="small",loc="best")  #顯示圖例 
            
            else:  #圖表繪圖後端設定為Plotly
                if x!="連續9點在下邊":    #只讓圖例只顯示一個
                    self.fig_i_mr_chart.add_scatter(x=self.ooc.index,y=self.ooc[x],mode='markers',name="9pts One-side",marker=dict(color="#EF4444",symbol="x"),showlegend=False) #標上連續9點在上邊(下邊)的點，不顯示圖例，顏色：警示紅
                else:
                    self.fig_i_mr_chart.add_scatter(x=self.ooc.index,y=self.ooc[x],mode='markers',name="9pts One-side",marker=dict(color="#EF4444",symbol="x"))  #標上連續9點在上邊(下邊)的點，顏色：警示紅               
  
        return None


#畫出所有機台的Boxplot
def boxplot_chart(process_raw_data,set_plot_backend):
    """
    1.畫出所有機台的Boxplot
    2.具有圖表繪圖後端切換功能
    """
        
    if  set_plot_backend=="Matplotlib":       #切換圖表繪圖後端   
        m_yield_data={}      #使用字典儲存所有機台Yield分組資料，供Matplotlib Boxplot使用
        for x in all_m_name:
            m_yield_data[x]=process_raw_data.groupby("Machine").get_group(x)["Yield"] 
            
        fig_boxplot,ax=plt.subplots()
        ax.boxplot(m_yield_data.values(),
                   labels=["機台"+x for x in all_m_name]
                   )
        
    else:       #圖表繪圖後端設定為Plotly
        m_yield_data=process_raw_data[["Machine","Yield"]]   #使用DataFrame儲存所有機台Yield分組資料，供Plotly Boxplot使用
        m_yield_data["Machine"]= "機台" + m_yield_data["Machine"].astype(str) #Machine欄位所有元素加上機台兩字
        
        fig_boxplot=go.Figure()
        fig_boxplot.update_layout(template='simple_white')  #圖片主題設定
        fig_boxplot.update_layout(margin=dict(t=10,b=10,l=10,r=10)) #調整繪圖區大小
        fig_boxplot.update_layout(xaxis=dict(showline=True,mirror=True,linewidth=1,linecolor="#808080"), #繪圖區邊框，顏色：正灰色
                                  yaxis=dict(showline=True,mirror=True,linewidth=1,linecolor="#808080"),  
                                  )
        fig_boxplot.update_layout(xaxis=dict(ticks="outside",tickwidth=1,tickcolor="#808080"),   #設定刻度線，顏色：正灰色
                                  yaxis=dict(ticks="outside",tickwidth=1,tickcolor="#808080")
                                  )  
        fig_boxplot.update_layout(font=dict(family="Microsoft JhengHei")) #設定字型
        fig_boxplot.add_box(x=m_yield_data["Machine"],y=m_yield_data["Yield"],boxpoints="outliers",boxmean=True, 
                            marker=dict(color="#EF4444",size=10),   #Outliers：設定警示紅
                            line=dict(color="#3B82F6", width=2),    #箱體外框：經典科技藍
                            fillcolor="rgba(59, 130, 246, 0.2)",     #具有80%透明感的經典科技藍  
                            width=0.5)       #箱子佔自己的格子50%
        
    return fig_boxplot
#%%

#計算各機台的統計量：平均、標準差、上界、下界。主畫面中間顯示用
def m_yield_stats(groups):
    """
    計算各機台的統計量：平均、標準差、上界、下界，並產生一個DataFrame表格
    """
    
    m_yield_stat_results=groups["Yield"].agg(["mean","std"])
    m_yield_stat_results.columns=["Mean","Std Dev"]  
    
    q1=groups["Yield"].quantile(0.25)  #找出各機台Box Plot的Q1
    q3=groups["Yield"].quantile(0.75)  #找出各機台Box Plot的Q3
    
    iqr=q3-q1 #IQR=Q3-Q1
    
    upper_fence=q3+1.5*iqr #算出各機台Boxplot的上界線   
    lower_fence=q1-1.5*iqr #算出各機台Boxplot的下界線    
    
    m_yield_stat_results["上界"]=upper_fence
    m_yield_stat_results["下界"]=lower_fence
    
    return m_yield_stat_results


#找出所有機台可能的異常Lot
def outlier_detection(process_raw_data):
    """
    找出所有機台可能的異常Lot
    """
    
    groups=process_raw_data.groupby("Machine")
    q1=groups["Yield"].transform(lambda x:x.quantile(0.25)) #找出Box Plot的Q1
    q3=groups["Yield"].transform(lambda x:x.quantile(0.75)) #找出Box Plot的Q3
    iqr=q3-q1 #IQR=Q3-Q1
    upper_fence=q3+1.5*iqr #算出Boxplot的上界線
    lower_fence=q1-1.5*iqr #算出Boxplot的下界線
    #找出超出上界，超出下界的Lot
    yield_outlier=process_raw_data.loc[(process_raw_data["Yield"]>upper_fence)|
                                       (process_raw_data["Yield"]<lower_fence)
                                       ]
    return yield_outlier




#判斷機台是否有差異
def machine_comparison(process_raw_data,groups,all_m_name):
    """
    1.使用利用Kruskal-Wallis Test判斷機台間平均是否有差異
    2.利用Dunn's Test將機台分組
    3.輸出比較後的結果(str)
    """ 
    #利用kruskal-Wallis Test檢查機台之間是否存在機差
    kruskal_results=pd.DataFrame()        
    m_data_list=[np.array(groups.get_group(item)["Yield"]) for i,item in enumerate(all_m_name)]
    
    stat,p_value=stats.kruskal(*m_data_list)
    kruskal_results.loc["kruskal_results","Stats"]=stat
    kruskal_results.loc["kruskal_results","P-value"]=p_value
        
    kruskal_results.loc["kruskal_results","顯著性差異"]="有" if kruskal_results.loc["kruskal_results","P-value"] < 0.05 else "無"
  
    
    if kruskal_results.loc["kruskal_results","顯著性差異"]=="無":
        m_comparison_result=f"🟢不同機台間的平均Yield無顯著差異(p-value = {p_value:.4f}>=0.05)" 
    else:   #有顯著性差異，需要找出有差異的機台

        if p_value<0.05:    #需要找出有差異的機台
            #使用Dunn's Test產出事後成對比較表
            dunn_results = sp.posthoc_dunn(a=process_raw_data,
                                            val_col="Yield", 
                                            group_col="Machine", 
                                            p_adjust="bonferroni" )
            
            #從事後成對比較表整理出結果
            classify=[] #記錄機台分組結果
            for i,item in enumerate(all_m_name):   #將相同的性能的機台分在同一組，p-vaule>=0.05為T
                temp_list=dunn_results[dunn_results[item]>=0.05].index.tolist()
               
                if temp_list not in classify:   #[B,A]與[A,B]相同，不記錄
                    classify.append(temp_list)  
          
        
            if len(classify)==2 and (len(classify[0]) != len(classify[1])) and (1 in (len(classify[0]),len(classify[1]))):    #分兩組，且只有一組為1，表示只有1台機台其它不同 [[A],[C,D]]
                temp=[classify[i] for i,item in enumerate(classify) if len(item)==1]     
                m_comparison_result=f"🔴機台{temp[0][0]}與其它台不同"
                
            elif len(classify)==1:      #表示所有機台沒有差異
                m_comparison_result=f"🟢所有機台沒有差異"
            
            else:       #分超過或等於兩組，且每一組都不相同，也沒有只有一組為1。[[A,B],[C,D]]或[[A],[B],[C,D]]。      
                temp=[f"({','.join(item)})" for i,item in enumerate(classify)]  #拆掉一層List，改成[(,),(,)]
                m_comparison_result=f"🟠存在多組差異：{'、'.join(temp)}"  #顯示結果為(,)、(,)
    
    return m_comparison_result


#判斷機台那台最穩定與最不穩定
def stabiliy_assessment(groups):
    """
    使用CV判斷那台機台最穩定與最不穩定
    """
    #找出機台的Yield平均與標準差之最大與最小
    m_yield_mean_std=groups["Yield"].agg(["mean","std"])
    m_yield_mean_std["cv"]=m_yield_mean_std["std"] / m_yield_mean_std["mean"]*100

       
    #判斷最穩定的機台        
    max_cv=m_yield_mean_std["cv"].idxmax()
    max_cv_value=m_yield_mean_std.loc[max_cv,"cv"]
    
    min_cv=m_yield_mean_std["cv"].idxmin()
    min_cv_value=m_yield_mean_std.loc[min_cv,"cv"]
    
    m_stabiliy={}
    m_stabiliy["最穩定機台"]=f"🟢機台{min_cv}最穩定：CV={min_cv_value:.2f}%"
    m_stabiliy["最不穩定機台"]=f"🔴機台{max_cv}最不穩定：CV={max_cv_value:.2f}%"

    return m_stabiliy      




#相關係數(看自變數之間與自變數與因變數的)
def corr(groups,selected_m_name,all_x,rv):    
    """
    1.相關係數(看自變數之間與自變數與因變數的)，產生corr_matrix
    2.將corr_matrix加上偏迴歸係數檢定，觀查共同變異
    """
    input_data=groups.get_group(selected_m_name)  
    corr_matrix=input_data.corr(numeric_only=True)  #非數值欄位不做相關係數分析
    corr_matrix=corr_matrix.loc[all_x,all_x+[rv]]   #看各自變數之間、各自變數與因變數
    
    #取各自變數與因變數的偏迴歸係數檢定，觀查共同變異
    srf_results=srf(groups,selected_m_name,rv,all_x) 
    coef_df = pd.read_html(srf_results.summary().tables[1].as_html(),index_col=0,header=0)[0]   #取出OLS Regression Results的第二張表
    
    #將corr_matrix加上偏迴歸係數檢定，觀查共同變異
    temp_list=[("有顯著相關" if item <0.05 else "無顯著相關") for i,item in enumerate(coef_df["P>|t|"]) if i>0] #將p-vaule的結果併入corr_matrix，排除Intercept
    corr_matrix["OLS P>|t|"]=temp_list
    
    return corr_matrix
    
    



#使用迴歸分析，找出機台樣本估計模型SRF
def srf(groups,selected_m_name,rv,selected_x):
    """
    一次載入一機台資料，找出指定自變數與因變數的樣本估計模型
    """
    #載入分析數據
    input_data=groups.get_group(selected_m_name)
        
    #迴歸分析
    #if len(selected_x)==1:
        #x=selected_x[0]
    #else:
    x="+".join(selected_x)  #整併選擇的自變數
    formula=f"{rv} ~ {x}"   #設定Formula
    yield_model=ols(formula,data=input_data)   
    yield_results=yield_model.fit()

    return yield_results

    
#全子集迴歸
def subset_regression(groups,selected_m_name,rv,all_x):
    """
    1.產生自變數所有的可能組合，將所有可能組合載入srf函數，並算出全子集迴歸
    2.統計指標有RSE、adj. R-squared
    """
    x_combinations=[list(itertools.combinations(all_x,i+1)) for i,item in enumerate(all_x)]  #產生自變數所有的可能組合
    
    model_metrics_list=pd.DataFrame() #收集所有子集的統計指標用
    for i,item_i in enumerate(x_combinations):  #將丟入srf計算RSE與adj.R-squared
        for j,item_j in enumerate(x_combinations[i]):   
            
            srf_results=srf(groups,selected_m_name,rv,item_j)
            
            x="+".join(item_j)  #整併選擇的自變數
            model_metrics_list.loc[x,"RSE"]=np.sqrt(srf_results.mse_resid)     #計算RSE，並收集
            model_metrics_list.loc[x,"adj. R-squared"]=srf_results.rsquared_adj  #計算adj.R-squared，並收集
    return model_metrics_list



#=======================主畫面===========================
#I-MR Chart 的畫面(最上)
top_r_col,top_l_col=st.columns(2) 
with top_r_col:             
    st.subheader("📊I-MR Chart")

    tabs=st.tabs(all_m_name)    #動態生成頁籤
    for i,tab in enumerate(tabs):   #每一個頁籤的內容
   
       with tab:     
        imr_chart=I_mr_chart(groups,all_m_name[i],rv,set_plot_backend)  #監控Yield的I-MR Chart
        if rule1_chk:
            imr_chart.ooc_rule()
        if rule2_chk:
            imr_chart.six_point_trend_rule()
        if rule3_chk:
            imr_chart.night_point_rule()
        
        if  set_plot_backend=="Matplotlib":       #切換圖表繪圖後端    
            st.pyplot(imr_chart.fig_i_mr_chart)    
            
        else:           #圖表繪圖後端設定為Plotly
            with st.container(border=True):     
                st.plotly_chart(imr_chart.fig_i_mr_chart,use_container_width=True) 

with top_l_col:            
    st.markdown("<h3>&nbsp;</h3>", unsafe_allow_html=True)  #保留高度用

    tabs=st.tabs(all_m_name)    #動態生成頁籤
    for i,tab in enumerate(tabs):   #每一個頁籤的內容

       with tab:
           imr_chart=I_mr_chart(groups,all_m_name[i],selected_rv,set_plot_backend)  #監控機台參數的I-MR Chart
           if rule1_chk:
               imr_chart.ooc_rule()
           if rule2_chk:
                imr_chart.six_point_trend_rule()
           if rule3_chk:
                imr_chart.night_point_rule()
                
           if  set_plot_backend=="Matplotlib":       #切換圖表繪圖後端                    
               st.pyplot(imr_chart.fig_i_mr_chart)    
               
           else:           #圖表繪圖後端設定為Plotly
               with st.container(border=True):
                   st.plotly_chart(imr_chart.fig_i_mr_chart,use_container_width=True) 
   
st.divider()

#Yield Boxplot的畫面(中間-上)
mid_1_l_col,mid_1_r_col=st.columns(2)    
with mid_1_l_col:          #Yield Boxplot
    st.subheader("📦Yield Boxplot")

    if  set_plot_backend=="Matplotlib":       #切換圖表繪圖後端       
        fig_boxplot=boxplot_chart(process_raw_data,set_plot_backend)

        st.pyplot(fig_boxplot) 
        
    else:           #圖表繪圖後端設定為Plotly
        fig_boxplot=boxplot_chart(process_raw_data,set_plot_backend)
        
        with st.container(border=True):
            st.plotly_chart(fig_boxplot,use_container_width=True) 
    
with mid_1_r_col:          #Machine Statistics Overview：平均、標準差、上界、下界
    st.subheader("🌟M/C Yield Stats Overview")
    st.dataframe(m_yield_stats(groups).style.format("{:.2f}",subset=["Mean","Std Dev","上界","下界"]), #數據四捨五入到小數點後第二位
                 use_container_width=True)  #佔滿這個欄位的寬度
    

#Yield Boxplot的畫面(中間-下)
mid_2_l_col,mid_2_mid_col,mid_2_r_col=st.columns(3)    
with mid_2_l_col:  #顯示異常Lot
    st.subheader("🔥Outlier")
    lot_outlier=outlier_detection(process_raw_data)
    
    if lot_outlier.empty and  m_selected_name!=[]:      #沒有outliter時，使用，避免出錯
        st.dataframe(lot_outlier[["Machine","Defect","Yield"]])
        st.info("目前無異常 Lot")
    else:
        st.dataframe(lot_outlier[["Machine","Defect","Yield"]])    

with mid_2_mid_col:  #顯示所有機差比較(Yield)
    st.markdown("#### 🔍所有機差比較(Yield)")
    st.info(machine_comparison(process_raw_data,groups,all_m_name))

with mid_2_r_col:  #所有機台穩定度(Yield
    st.markdown("#### 🔍所有機台穩定度(Yield)")
    st.info(stabiliy_assessment(groups)["最穩定機台"])
    st.info(stabiliy_assessment(groups)["最不穩定機台"])    

        
st.divider()    
    
#迴歸分析的畫面(下面)
down_l_col,down_r_col=st.columns(2) 
with down_l_col:
    st.subheader("📈相關係數 + OLS P>|t|")

    tabs=st.tabs(all_m_name)    #動態生成頁籤
    for i,tab in enumerate(tabs):   #每一個頁籤的內容   
        with tab:     
            corr_matrix=corr(groups, all_m_name[i], all_x, rv) #相關係數矩陣
            st.dataframe(corr_matrix.style.format("{:.3f}",subset=all_x+[rv]),     #數據四捨五入到小數點後第三位
                         use_container_width=True)  #佔滿這個欄位的寬度

with down_r_col:
    st.subheader("🧬全子集迴歸")

    tabs=st.tabs(all_m_name)    #動態生成頁籤
    for i,tab in enumerate(tabs):   #每一個頁籤的內容   
        with tab:     
            model_matrics_list=subset_regression(groups,all_m_name[i],rv,all_x) #模型統計指標清單
            st.dataframe(model_matrics_list.style.format("{:.3f}",subset=["RSE","adj. R-squared"]),  #數據四捨五入到小數點後第三位
                         use_container_width=True)  
           
           
    
                     
        
    







