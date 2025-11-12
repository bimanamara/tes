# di modules/components.py
import streamlit as st

def hero(title: str, subtitle: str = ""):
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, rgba(14, 165, 233, 0.95), rgba(6, 182, 212, 0.95));
            padding: 4rem 3rem;
            border-radius: 24px;
            margin-bottom: 3rem;
            box-shadow: 0 20px 60px rgba(14, 165, 233, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.3);
            backdrop-filter: blur(20px);
            position: relative;
            overflow: hidden;
        ">
            <div style="
                position: absolute;
                top: -50%;
                right: -50%;
                width: 200%;
                height: 200%;
                background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
                animation: pulse 4s ease-in-out infinite;
            "></div>
            <h1 style="
                color: white;
                font-size: 3.5rem;
                font-weight: 900;
                margin: 0 0 1rem 0;
                letter-spacing: -2px;
                text-shadow: 0 4px 20px rgba(0,0,0,0.2);
                position: relative;
                z-index: 1;
            ">{title}</h1>
            <p style="
                color: rgba(255,255,255,0.95);
                font-size: 1.25rem;
                margin: 0;
                font-weight: 500;
                letter-spacing: 0.5px;
                line-height: 1.8;
                position: relative;
                z-index: 1;
            ">{subtitle}</p>
        </div>
        <style>
            @keyframes pulse {{
                0%, 100% {{ transform: scale(1); }}
                50% {{ transform: scale(1.1); }}
            }}
        </style>
        """,
        unsafe_allow_html=True
    )

def kpi(label: str, value: str, delta: str = "", delta_color: str = "normal"):
    delta_colors = {
        "normal": "#6b7280",
        "positive": "#10b981",
        "negative": "#ef4444"
    }
    
    delta_icon = ""
    if delta:
        if delta_color == "positive":
            delta_icon = "↗"
        elif delta_color == "negative":
            delta_icon = "↘"
    
    delta_html = f"""
        <div style="
            font-size: 0.875rem;
            color: {delta_colors.get(delta_color, delta_colors['normal'])};
            font-weight: 700;
            margin-top: 0.75rem;
            display: flex;
            align-items: center;
            gap: 0.25rem;
        ">{delta_icon} {delta}</div>
    """ if delta else ""
    
    st.markdown(
        f"""
        <div style="
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px) saturate(180%);
            padding: 2rem;
            border-radius: 20px;
            border: 1px solid rgba(203, 213, 225, 0.5);
            box-shadow: 0 8px 32px rgba(14, 165, 233, 0.15);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        " onmouseover="
            this.style.transform='translateY(-12px) scale(1.03)'; 
            this.style.boxShadow='0 24px 64px rgba(14, 165, 233, 0.25)';
        " 
        onmouseout="
            this.style.transform='translateY(0) scale(1)'; 
            this.style.boxShadow='0 8px 32px rgba(14, 165, 233, 0.15)';
        ">
            <div style="
                position: absolute;
                top: 0;
                right: 0;
                width: 100px;
                height: 100px;
                background: linear-gradient(135deg, rgba(14, 165, 233, 0.1), transparent);
                border-radius: 0 20px 0 100%;
            "></div>
            <div style="
                font-size: 0.688rem;
                font-weight: 900;
                color: #64748b;
                text-transform: uppercase;
                letter-spacing: 1.5px;
                margin-bottom: 0.75rem;
            ">{label}</div>
            <div style="
                font-size: 3rem;
                font-weight: 900;
                background: linear-gradient(135deg, #0ea5e9, #06b6d4);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                letter-spacing: -2px;
                line-height: 1;
            ">{value}</div>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True
    )
