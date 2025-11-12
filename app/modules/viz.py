import plotly.express as px
import plotly.graph_objects as go
import pandas as pd, numpy as np

def get_base_layout(title: str):
    layout = {
        "title": {
            "text": f"<b>{title}</b>",
            "font": {"size": 24, "color": "#0f172a", "family": "Inter"},
            "x": 0.5,
            "xanchor": "center",
            "y": 0.95,
            "yanchor": "top"
        },
        "autosize": True,
        "margin": {"l": 70, "r": 40, "t": 100, "b": 70},
        "plot_bgcolor": "rgba(248, 250, 252, 0.5)",
        "paper_bgcolor": "rgba(255, 255, 255, 0.95)",
        "font": {"family": "Inter", "size": 14, "color": "#1e293b"},
        "hoverlabel": {
            "bgcolor": "#ffffff",
            "font": {"size": 14, "color": "#0f172a", "family": "Inter"},
            "bordercolor": "#0ea5e9"
        },
        "xaxis": {
            "gridcolor": "rgba(203, 213, 225, 0.3)",
            "title_font": {"size": 16, "color": "#475569", "family": "Inter"},
            "tickfont": {"size": 13, "color": "#64748b"},
            "showline": True,
            "linecolor": "#cbd5e1",
            "linewidth": 2
        },
        "yaxis": {
            "gridcolor": "rgba(203, 213, 225, 0.3)",
            "title_font": {"size": 16, "color": "#475569", "family": "Inter"},
            "tickfont": {"size": 13, "color": "#64748b"},
            "showline": True,
            "linecolor": "#cbd5e1",
            "linewidth": 2
        }
    }
    return layout

def heatmap(df: pd.DataFrame, title: str):
    fig = px.imshow(
        df, 
        aspect="auto", 
        labels=dict(color="Value"),
        color_continuous_scale=["#dbeafe", "#3b82f6", "#1e3a8a"]
    )
    fig.update_layout(**get_base_layout(title))
    fig.update_traces(
        texttemplate="<b>%{z:.2f}</b>",
        textfont={"size": 12, "color": "#ffffff", "family": "Inter"}
    )
    fig.update_xaxes(tickangle=-45)
    fig.update_coloraxes(colorbar=dict(
        thickness=20,
        outlinewidth=2,
        outlinecolor="#cbd5e1",
        tickfont={"size": 12}
    ))
    return fig

def barh(series: pd.Series, title: str, xlab="Value"):
    s = series.sort_values(ascending=True)
    
    fig = px.bar(
        x=s.values, 
        y=s.index, 
        orientation='h',
        labels={"x": xlab, "y": ""}
    )
    
    fig.update_traces(
        marker=dict(
            color=s.values,
            colorscale=[[0, "#dbeafe"], [0.5, "#3b82f6"], [1, "#1e40af"]],
            line=dict(color="#ffffff", width=2)
        ),
        texttemplate='<b>%{x:.2f}</b>',
        textposition='outside',
        textfont={"size": 13, "color": "#0f172a", "family": "Inter"}
    )
    
    fig.update_layout(**get_base_layout(title))
    fig.update_yaxes(tickfont={"size": 13})
    return fig

def bars(x, y, title: str, xlab="X", ylab="Y"):
    fig = px.bar(
        x=x, 
        y=y, 
        labels={"x": xlab, "y": ylab}
    )
    
    fig.update_traces(
        marker=dict(
            color=y,
            colorscale=[[0, "#a78bfa"], [0.5, "#8b5cf6"], [1, "#6d28d9"]],
            line=dict(color="#ffffff", width=2)
        ),
        texttemplate='<b>%{y:.2f}</b>',
        textposition='outside',
        textfont={"size": 13, "color": "#0f172a", "family": "Inter"}
    )
    
    fig.update_layout(**get_base_layout(title))
    fig.update_xaxes(tickangle=-45, tickfont={"size": 12})
    return fig

def cause_effect_scatter(r: pd.Series, c: pd.Series, title="Cause-Effect Diagram"):
    df = pd.DataFrame({
        "relation": r - c,
        "prominence": r + c,
        "id": r.index
    })
    
    fig = px.scatter(
        df, 
        x="relation", 
        y="prominence", 
        text="id",
        size="prominence",
        color="prominence",
        color_continuous_scale=["#fca5a5", "#fbbf24", "#34d399"]
    )
    
    fig.update_layout(**get_base_layout(title))
    fig.update_traces(
        mode='markers+text',
        textposition='top center',
        textfont={"size": 12, "color": "#0f172a", "family": "Inter"},
        marker={"line": {"width": 3, "color": "#ffffff"}, "opacity": 0.9}
    )
    return fig

def radar_weights(weights: pd.Series, title="Criteria Radar"):
    s = weights.sort_values(ascending=False).head(8)
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=s.values,
        theta=s.index,
        fill='toself',
        name='weight',
        fillcolor='rgba(14, 165, 233, 0.4)',
        line={"color": "#0ea5e9", "width": 4},
        marker={"size": 10, "color": "#0ea5e9", "line": {"width": 2, "color": "#ffffff"}}
    ))
    
    layout = get_base_layout(title)
    layout["polar"] = {
        "radialaxis": {
            "visible": True,
            "gridcolor": "rgba(203, 213, 225, 0.5)",
            "tickfont": {"size": 12, "color": "#64748b"},
            "linecolor": "#cbd5e1",
            "linewidth": 2
        },
        "angularaxis": {
            "tickfont": {"size": 13, "color": "#0f172a", "family": "Inter"},
            "linecolor": "#cbd5e1",
            "linewidth": 2
        },
        "bgcolor": "rgba(248, 250, 252, 0.5)"
    }
    fig.update_layout(**layout)
    return fig

def sankey_criteria(Td: pd.DataFrame, title="Criteria Influence Sankey"):
    labels = Td.index.tolist()
    source, target, value = [], [], []
    
    for i, a in enumerate(labels):
        for j, b in enumerate(labels):
            if i == j:
                continue
            v = float(Td.iloc[i, j])
            if v > 0:
                source.append(i)
                target.append(j)
                value.append(v)
    
    colors = ["#3b82f6", "#8b5cf6", "#ec4899", "#f97316", "#10b981", "#06b6d4", "#f59e0b", "#ef4444"]
    node_colors = [colors[i % len(colors)] for i in range(len(labels))]
    
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            label=labels,
            pad=25,
            thickness=30,
            line=dict(color="#ffffff", width=3),
            color=node_colors
        ),
        link=dict(
            source=source,
            target=target,
            value=value,
            color="rgba(14, 165, 233, 0.2)"
        )
    )])
    
    layout = get_base_layout(title)
    layout["font"]["size"] = 13
    fig.update_layout(**layout)
    return fig
