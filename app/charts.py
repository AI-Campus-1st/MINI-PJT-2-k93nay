# app/charts.py
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

def create_scatter_matrix(df):
    """절대수요와 상대밀도를 교차 검증하는 핵심 산점도"""
    fig = px.scatter(
        df,
        x="final_volume_score",
        y="youth_share_pct",
        text="dong_name",
        size="avg_youth_pop",
        color="final_priority_score",
        color_continuous_scale="Viridis",
        labels={
            "final_volume_score": "행정동별 청년 절대인구 수 기준 규모 점수 (Volume)",
            "youth_share_pct": "행정동별 청년 인구 점유율 (%) (Density)",
            "final_priority_score": "종합 유망도"
        },
        title="<b>SH 청년매입임대 공급 후보지 교차 검증 매트릭스</b>"
    )
    
    
    fig.update_traces(textposition='top center', marker=dict(line=dict(width=1, color='DarkSlateGrey')))
    
    # 의사결정 사면(Matrix) 분할선 추가 (평균치 기준 사면 구분)
    avg_x = df["final_volume_score"].mean()
    avg_y = df["youth_share_pct"].mean()
    
    fig.add_vline(x=avg_x, line_width=1.5, line_dash="dash", line_color="gray")
    fig.add_hline(y=avg_y, line_width=1.5, line_dash="dash", line_color="gray")
    
    fig.update_layout(
        plot_bgcolor="rgba(240,240,240,0.5)",
        margin=dict(l=20, r=20, t=50, b=20),
        height=500
    )
    return fig

def create_priority_bar(df):
    """최종 종합 유망도 랭킹 세로 바 차트"""
    # 점수 높은 순 정렬
    df_sorted = df.sort_values(by="final_priority_score", ascending=True)
    
    fig = px.bar(
        df_sorted,
        x="final_priority_score",
        y="dong_name",
        orientation='h',
        color="final_priority_score",
        color_continuous_scale="Cividis",
        labels={"final_priority_score": "종합 공급 유망도 스코어", "dong_name": "행정동명"},
        title="<b>행정동별 종합 랭킹</b>"
    )
    fig.update_layout(height=450, showlegend=False, margin=dict(l=20, r=20, t=50, b=20))
    return fig
