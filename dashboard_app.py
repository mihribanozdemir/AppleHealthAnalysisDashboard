import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import zipfile
import io


st.set_page_config(
    page_title="Health Analysis Dashboard",
    initial_sidebar_state="expanded",
)

tab1, tab2, tab3, tab4, tab5= st.tabs([ "Genel Bakış :compass:","Aktivite Sayfası :woman-running:", "Kalp & Vucüt Sağlığı :anatomical_heart:", "Uyku Sayfası :sleeping:", "İlişkisel Analiz 📊"])

with st.sidebar:
    st.sidebar.title("Veri Yükle")
    zip_file = st.sidebar.file_uploader("Verileri zip formatında yükleyiniz." ,type="zip")
    if zip_file is not None:
        if "uploaded_data" not in st.session_state:
            st.session_state.uploaded_data = {}
        if "last_uploaded_zip" not in  st.session_state or st.session_state.last_uploaded_zip != zip_file:
            with zipfile.ZipFile(zip_file) as z:
                file_names = z.namelist()
                st.write("Zip içerisindeki dosyalar:", file_names)
                for name in file_names:
                    if name.endswith(".csv"):
                        type_name = name.replace(".csv", "")  # örn: "StepCount"
                        with z.open(name) as f:
                            df = pd.read_csv(f)
                            st.session_state.uploaded_data[type_name] = df
            st.session_state.last_uploaded_zip = zip_file
    else:
        st.write("Lütfen zip dosyası yükleyiniz.")
if "uploaded_data" not in st.session_state or not st.session_state.uploaded_data:
    st.warning("Lütfen analiz yapmadan önce zip dosyası yükleyin.")
    st.stop()
# Grafikler
height = 176
custom_colors =  ["#fd7f6f", "#7eb0d5", "#b2e061", "#bd7ebe", "#ffb55a", "#ffee65", "#beb9db", "#fdcce5", "#8bd3c7"]


@st.cache_data
def get_step_grouped_data(df, x_column):
    df = df.copy()
    if x_column == "dow":
        ordered_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        df["dow"] = pd.Categorical(df["dow"], categories=ordered_days, ordered=True)
    elif x_column == "month_name":
        ordered_months = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        df["month_name"] = pd.Categorical(df["month_name"], categories=ordered_months, ordered=True)

    return df.groupby([x_column, "sourceName"])["value"].sum().reset_index()

def plot_step_chart(grouped_df, x_column, title="Adım Verisi"):
    fig = px.line(
        grouped_df,
        x=x_column,
        y="value",
        color="sourceName",
        labels={
            "value": "Adım Sayısı",
            "date": "Tarih",
            "sourceName": "Kaynak"
        },
        title=title,
        color_discrete_sequence=custom_colors,
    )
    fig.update_traces(mode="lines+markers")
    st.plotly_chart(fig, use_container_width=True)

@st.cache_data
def get_grouped_distance(df, group_col):
    df = df.copy()
    df["startDate"] = pd.to_datetime(df["startDate"])

    if group_col == "dow":
        df["dow"] = df["startDate"].dt.day_name()
        df["dow"] = pd.Categorical(
            df["dow"],
            categories=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
            ordered=True
        )
    elif group_col == "month_name":
        df["month_name"] = df["startDate"].dt.strftime("%B")
        df["month_name"] = pd.Categorical(
            df["month_name"],
            categories=[
                "January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December"
            ],
            ordered=True
        )
    elif group_col == "year":
        df["year"] = df["startDate"].dt.year
    elif group_col == "hour":
        df["hour"] = df["startDate"].dt.hour
    elif group_col == "date":
        df["date"] = df["startDate"].dt.date
    else:
        raise ValueError(f"'{group_col}' desteklenmeyen bir grup kolonudur.")

    return df.groupby([group_col, "sourceName"])["value"].sum().reset_index()

def plot_monthly_distance(df_grouped):
    fig = px.bar(
        df_grouped,
        x="month_name",
        y="value",
        color="sourceName",
        barmode="group",
        labels={"value": "Walking Distance (km)", "month_name": "Month"},
        title="Monthly Walking Distance by Source",
        color_discrete_sequence=custom_colors
    )
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

def plot_daily_distance(df_grouped):
    fig = px.line(
        df_grouped,
        x="date",
        y="value",
        color="sourceName",
        markers=True,
        labels={"date": "Tarih", "value": "Mesafe (km)", "sourceName": "Cihaz"},
        title="📅 Günlük Yürüyüş Mesafesi",
        color_discrete_sequence=custom_colors
    )
    fig.update_layout(xaxis_title="Tarih", yaxis_title="Mesafe")
    st.plotly_chart(fig, use_container_width=True)

def plot_dow_distance(grouped_df):
    fig = px.bar(
        grouped_df,
        x="dow",
        y="value",
        color="sourceName",
        barmode="group",
        labels={"value": "Yürüme Mesafesi (km)", "day_name": "Gün"},
        title="Haftanın Gününe Göre Yürüme Mesafesi (Cihaz Kaynağına Göre)",
        color_discrete_sequence=custom_colors
    )
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)


@st.cache_data
def get_metric_grouped(df, group_col):
    df = df.copy()
    df["startDate"] = pd.to_datetime(df["startDate"])

    if group_col == "date":
        df["date"] = df["startDate"].dt.date
        return df.groupby(["date", "sourceName"])["value"].mean().reset_index()

    elif group_col == "dow":
        df["dow"] = df["startDate"].dt.day_name()
        df["dow"] = pd.Categorical(df["dow"], categories=[
            "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
        ], ordered=True)
        return df.groupby(["dow", "sourceName"])["value"].mean().reset_index()

    else:
        raise ValueError("Desteklenmeyen grup kolon adı.")

def plot_speed_daily(df_grouped):
    fig = px.line(
        df_grouped,
        x="date",
        y="value",
        color="sourceName",
        labels={"value": "Yürüme Hızı (km/h)", "date": "Tarih"},
        color_discrete_sequence=custom_colors,
        title="Günlük Ortalama Yürüme Hızı (Kaynağa Göre)"
    )
    fig.update_traces(mode="lines+markers")
    fig.update_layout(hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

def plot_speed_by_dow(df_grouped):
    fig = px.bar(
        df_grouped,
        x="dow",
        y="value",
        text_auto=".2f",
        title="Haftanın Gününe Göre Ortalama Yürüme Hızı",
        labels={"dow": "Gün", "value": "Hız (km/h)", "sourceName": "Kaynak"},
        color_discrete_sequence=custom_colors
    )
    fig.update_layout(xaxis_title="Gün", yaxis_title="Hız (km/h)")
    st.plotly_chart(fig, use_container_width=True)

def plot_step_length_daily(df_grouped):
    fig = px.line(
        df_grouped,
        x="date",
        y="value",
        markers=True,
        title="Günlük Ortalama Adım Uzunluğu",
        labels={"date": "Tarih", "value": "Adım Uzunluğu (cm)"},
        color_discrete_sequence=custom_colors
    )
    fig.update_layout(xaxis_title="Tarih", yaxis_title="Adım Uzunluğu (cm)")
    st.plotly_chart(fig, use_container_width=True)

@st.cache_data
def get_heart_rate_grouped(df):
    df = df.copy()
    df["startDate"] = pd.to_datetime(df["startDate"])
    df["date"] = df["startDate"].dt.date
    return df.groupby(["date", "sourceName"])["value"].mean().reset_index()

def plot_heart_rate_daily(df_grouped):
    fig = px.line(
        df_grouped,
        x="date",
        y="value",
        color="sourceName",
        markers=True,
        title="Günlük Ortalama Nabız Değeri (Kaynağa Göre)",
        color_discrete_sequence=custom_colors,
        labels={"value": "BPM", "date": "Tarih", "sourceName": "Kaynak"}
    )
    fig.update_layout(xaxis_title="Tarih", yaxis_title="BPM", hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

@st.cache_data
def get_weight_monthly_avg(df):
    df = df.copy()
    df["startDate"] = pd.to_datetime(df["startDate"], errors="coerce")
    df["month"] = df["startDate"].dt.month
    df = df.sort_values("startDate")
    return df.groupby("month")["value"].mean().reset_index()

def plot_weight_by_month(grouped):
    fig = px.bar(
        grouped, x="month", y="value",
        title="📊 Aylık Kilo Değişimi (Ortalama kg)",
        color_discrete_sequence=custom_colors
    )
    fig.update_layout(xaxis_title="Ay", yaxis_title="Kilo (kg)")
    st.plotly_chart(fig, use_container_width=True)

@st.cache_data
def calculate_bmi(df, height):
    df = df.copy()
    df["BMI"] = df["value"] / ((height / 100) ** 2)
    df["date"] = pd.to_datetime(df["startDate"]).dt.date
    return df

def plot_bmi_line(df):
    fig = px.line(
        df, x="date", y="BMI", markers=True,
        title="📈 BMI Değeri Zaman Serisi",
        color_discrete_sequence=custom_colors
    )
    fig.update_layout(xaxis_title="Tarih", yaxis_title="BMI")
    st.plotly_chart(fig, use_container_width=True)

@st.cache_data
def get_daily_total_energy(active_df, basal_df):
    active_df = active_df.copy()
    basal_df = basal_df.copy()
    active_df["startDate"] = pd.to_datetime(active_df["startDate"], errors="coerce")
    basal_df["startDate"] = pd.to_datetime(basal_df["startDate"], errors="coerce")

    active_daily = active_df.groupby(active_df["startDate"].dt.date)["value"].sum().reset_index(name="Aktif Kalori")
    basal_daily = basal_df.groupby(basal_df["startDate"].dt.date)["value"].sum().reset_index(name="Bazal Kalori")

    combined = pd.merge(active_daily, basal_daily, on="startDate", how="outer").fillna(0)
    combined["Toplam Kalori"] = combined["Aktif Kalori"] + combined["Bazal Kalori"]
    return combined.sort_values("startDate")

def plot_daily_total_energy(combined):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=combined["startDate"], y=combined["Aktif Kalori"], mode="lines+markers", name="Aktif Kalori"))
    fig.add_trace(go.Scatter(x=combined["startDate"], y=combined["Bazal Kalori"], mode="lines+markers", name="Bazal Kalori"))
    fig.add_trace(go.Scatter(x=combined["startDate"], y=combined["Toplam Kalori"], mode="lines+markers", name="Toplam Kalori", line=dict(width=3, dash="dash")))

    fig.update_layout(
        title="🔥 Günlük Toplam Kalori Harcaması",
        xaxis_title="Tarih",
        yaxis_title="Kalori (kcal)",
        hovermode="x unified",
        template="plotly_white"
    )
    st.plotly_chart(fig, use_container_width=True)

@st.cache_data
def get_active_energy_by_dow(df):
    df = df.copy()
    df["startDate"] = pd.to_datetime(df["startDate"], errors="coerce")
    df["dow"] = df["startDate"].dt.day_name()
    df["dow"] = pd.Categorical(df["dow"], categories=[
        "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
    ], ordered=True)
    return df.groupby("dow")["value"].mean().reset_index()

def plot_active_energy_by_dow(grouped_df):
    fig = px.bar(
        grouped_df,
        x="dow",
        y="value",
        title="Haftanın Günlerine Göre Ortalama Aktif Kalori",
        labels={"dow": "Gün", "value": "Ortalama Kalori (kcal)"},
        color_discrete_sequence=custom_colors
    )
    fig.update_layout(xaxis_title="Gün", yaxis_title="Ortalama Kalori (kcal)")
    st.plotly_chart(fig, use_container_width=True)


def plot_vo2max(df):
    df["date"] = pd.to_datetime(df["startDate"], errors="coerce").dt.date
    vo2_avg = df.groupby("date")["value"].mean().reset_index()
    fig = px.line(vo2_avg, x="date", y="value", title="VO2Max Zaman Serisi", labels={"value": "VO2Max", "date": "Tarih"})
    st.plotly_chart(fig, use_container_width=True)

def plot_single_metric(df, title, label):
    df["date"] = pd.to_datetime(df["startDate"], errors="coerce").dt.date
    daily = df.groupby("date")["value"].mean().reset_index()
    fig = px.line(daily, x="date", y="value", title=f"{title}", labels={"value": label, "date": "Tarih"})
    st.plotly_chart(fig, use_container_width=True)

@st.cache_data
def get_sleep_metrics(df):
    df = df.copy()
    df["startDate"] = pd.to_datetime(df["startDate"])
    df["endDate"] = pd.to_datetime(df["endDate"])
    df["start"] = df["startDate"]
    df["end"] = df["endDate"]
    df["date"] = df["start"].dt.date
    df["dow"] = df["start"].dt.day_name()
    daily_sleep = df.groupby("date")["sleep_duration_hours"].sum().reset_index()
    daily_sleep["dow"] = pd.to_datetime(daily_sleep["date"]).dt.day_name()
    avg_sleep_by_dow = (
        daily_sleep.groupby("dow")["sleep_duration_hours"]
        .mean()
        .reindex(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
        .reset_index(name="avg_sleep")
    )
    sleep_type_dist = df.groupby("sleep_type")["sleep_duration_hours"].mean().reset_index()

    return avg_sleep_by_dow, sleep_type_dist


def plot_avg_sleep_by_dow(df_grouped):
    fig = px.bar(
        df_grouped,
        x="dow",
        y="avg_sleep",
        title="🗓Haftalık Ortalama Uyku Süresi",
        color_discrete_sequence=custom_colors,
        labels={"dow": "Gün", "avg_sleep": "Ortalama Uyku Süresi (saat)"}
    )
    st.plotly_chart(fig, use_container_width=True)

def plot_sleep_type_pie(df_grouped):
    fig = px.pie(
        df_grouped,
        names="sleep_type",
        values="sleep_duration_hours",
        title="Uyku Evrelerine Göre Dağılım",
        color_discrete_sequence=custom_colors
    )
    st.plotly_chart(fig, use_container_width=True)


@st.cache_data
def normalize_date(df):
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.tz_localize(None).dt.floor("D")
    return df


def render_dashboard():
    if "uploaded_data" not in st.session_state:
        st.session_state["uploaded_data"] = {}

    step_df = st.session_state.get("step_count")
    if step_df is not None:
        step_df = step_df[step_df["sourceName"] == "Ali Haydar Akca’s iPhone"]
    heart_df = normalize_date(st.session_state.uploaded_data.get("HeartRate")) if st.session_state.uploaded_data.get("HeartRate") is not None else None
    active_df = normalize_date(st.session_state.uploaded_data.get("ActiveEnergyBurned")) if st.session_state.uploaded_data.get("ActiveEnergyBurned") is not None else None
    basal_df = normalize_date(st.session_state.uploaded_data.get("BasalEnergyBurned")) if st.session_state.uploaded_data.get("BasalEnergyBurned") is not None else None
    sleep_df = normalize_date(st.session_state.uploaded_data.get("SleepAnalysis")) if st.session_state.uploaded_data.get("SleepAnalysis") is not None else None
    if sleep_df is not None:
        sleep_df = sleep_df[sleep_df["sourceName"] == "Ali Haydar Akca’s iPhone"]
    speed_df = normalize_date(st.session_state.uploaded_data.get("WalkingSpeed")) if st.session_state.uploaded_data.get("WalkingSpeed") is not None else None

    step_avg = step_df.groupby("date")["value"].sum().mean() if step_df is not None else 0
    heart_rate_mean = heart_df.groupby("date")["value"].mean().mean() if heart_df is not None else 0
    sleep_avg = sleep_df.groupby("date")["sleep_duration_hours"].sum().mean() if sleep_df is not None else 0
    speed_avg = speed_df.groupby("date")["value"].mean().mean() if speed_df is not None else 0

    if active_df is not None and basal_df is not None:
        active_daily = active_df.groupby("date")["value"].sum()
        basal_daily = basal_df.groupby("date")["value"].sum()
        total_daily = active_daily.add(basal_daily, fill_value=0)
        avg_daily_calories = total_daily.mean()
    else:
        avg_daily_calories = 0

    # METRİK GÖSTERİMİ
    col1, col2, col3 = st.columns(3)
    col1.metric("❤️ Ortalama Nabız", f"{heart_rate_mean:.0f} BPM")
    col2.metric("👣 Ortalama Günlük Adım", f"{step_avg:.0f} adım")
    col3.metric("🔥 Günlük Ortalama Kalori", f"{avg_daily_calories:.0f} kcal")

    col4, col5 = st.columns(2)
    col4.metric("🛌 Ortalama Uyku Süresi", f"{sleep_avg:.2f} saat")
    col5.metric("🚶 Ortalama Yürüme Hızı", f"{speed_avg:.2f} km/h")

    # GRAFİK: Adım Sayısı (Son 7 Gün)
    if step_df is not None:
        daily_steps = step_df.groupby("date")["value"].sum().reset_index()
        fig = px.bar(
            daily_steps.tail(7),
            x="date",
            y="value",
            title="🦶 Son 7 Günlük Adım Dağılımı",
            color_discrete_sequence=custom_colors
        )
        fig.update_layout(xaxis_title="Tarih", yaxis_title="Adım Sayısı")
        st.plotly_chart(fig, use_container_width=True)

@st.cache_data
def preprocess_step_count(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["startDate"] = pd.to_datetime(df["startDate"], errors="coerce")
    df["date"] = df["startDate"].dt.floor("D")
    df["month_name"] = df["startDate"].dt.strftime("%B")
    df["year"] = df["startDate"].dt.year
    df["hour"] = df["startDate"].dt.hour
    df["dow"] = df["startDate"].dt.day_name()
    return df


with tab1:
    render_dashboard()

with tab2:
    sub_tab1, sub_tab2, sub_tab3 = st.tabs([
        "Adım Sayısı",
        "Yürüme Mesafesi",
        "Yürüme Hızı / Adım Uzunluğu"
    ])

    with sub_tab1:
        if "StepCount" in st.session_state.uploaded_data:
            step_count = preprocess_step_count(st.session_state.uploaded_data["StepCount"])
            st.session_state.step_count = step_count
        elif "step_count" in st.session_state:
            step_count = st.session_state["step_count"]
        else:
            st.warning("Adım verisi bulunamadı.")
            step_count = None
        source_options = step_count["sourceName"].dropna().unique().tolist()
        col1, col2 = st.columns([1, 1])
        with col1:
            selected_sources = st.multiselect(
                    "Kaynaklar",
                    options=source_options,
                    default=source_options,
                    key = "selected_sources"
                )
        with col2:
            view_options = ["Genel", "Aylık", "Yıllık", "Saatlik", "Haftanın Günü"]
            view_mode = st.selectbox("Zaman Görünümünü Seç", view_options, key="view_mode")

        filtered_df = step_count[step_count["sourceName"].isin(st.session_state.selected_sources)]
        if st.session_state.view_mode == "Genel":
                min_dt = filtered_df["date"].min().to_pydatetime()
                max_dt = filtered_df["date"].max().to_pydatetime()
                date_range = st.slider(
                    "Tarih Aralığı",
                    min_value=min_dt,
                    max_value=max_dt,
                    value=(min_dt, max_dt),
                    format="YYYY-MM-DD",
                    key = "activity_date_slider"
                )
                filtered = step_count[
                    (step_count["date"] >= date_range[0]) &
                    (step_count["date"] <= date_range[1])
                ]
                plot_step_chart(filtered, "date", title="Genel Adım Verisi")
                source_avg = step_count.groupby("sourceName")["value"].mean().reset_index().sort_values(by="value",ascending=False)
                st.dataframe(source_avg, use_container_width=True)
        elif st.session_state.view_mode == "Aylık":
                min_dt = filtered_df["date"].min().to_pydatetime()
                max_dt = filtered_df["date"].max().to_pydatetime()
                date_range = st.slider(
                    "Tarih Aralığı",
                    min_value=min_dt,
                    max_value=max_dt,
                    value=(min_dt, max_dt),
                    format="YYYY-MM-DD",
                    key="activity_date_slider_month"
                )
                filtered = step_count[
                    (step_count["date"] >= date_range[0]) &
                    (step_count["date"] <= date_range[1])
                    ]

                grouped = get_step_grouped_data(filtered, "month_name")
                plot_step_chart(grouped, "month_name", title="Aylık Adım Verisi")


        elif st.session_state.view_mode == "Yıllık":
                grouped = get_step_grouped_data(filtered_df, "year")
                plot_step_chart(grouped, "year", title="Yıllık Adım Verisi")
        elif st.session_state.view_mode == "Saatlik":
                grouped = get_step_grouped_data(filtered_df, "hour")
                plot_step_chart(grouped, "hour", title="Saatlik Adım Verisi")
        elif st.session_state.view_mode == "Haftanın Günü":
                grouped = get_step_grouped_data(filtered_df, "dow")
                plot_step_chart(grouped, "dow", title="Güne Göre Adım Verisi")


    with sub_tab2:
        if "DistanceWalkingRunner" in st.session_state.uploaded_data:
            distance_walking_runner = st.session_state.uploaded_data["DistanceWalkingRunner"] #km
            source_options = distance_walking_runner["sourceName"].dropna().unique().tolist()
            col1, col2 = st.columns([1, 1])
            with col1:
                selected_sources = st.multiselect(
                    "Cihaz Kaynağı",
                    options=source_options,
                    default=source_options,
                    key="dw_selected_sources"
                )

            with col2:
                view_mode = st.selectbox(
                    "Zaman Görünümü",
                    ["Aylık Yürüyüş Mesafesi", "Günlük Yürüyüş Zaman Serisi", "Haftanın Gününe Göre"],
                    key= "dw_view_mode"
                )
            filtered = distance_walking_runner[distance_walking_runner["sourceName"].isin(st.session_state.dw_selected_sources)]

            if st.session_state.dw_view_mode == "Aylık Yürüyüş Mesafesi":
                grouped = get_grouped_distance(filtered, group_col="month_name")
                plot_monthly_distance(grouped)
            elif st.session_state.dw_view_mode == "Günlük Yürüyüş Zaman Serisi":
                grouped = get_grouped_distance(filtered, group_col="date") #kontrol et
                plot_daily_distance(grouped)
            elif st.session_state.dw_view_mode == "Haftanın Gününe Göre":
                grouped = get_grouped_distance(filtered, group_col="dow")
                plot_dow_distance(grouped)

    with sub_tab3:
        if "WalkingSpeed" in st.session_state.uploaded_data and "WalkingStepLength" in st.session_state.uploaded_data:
            walking_speed = st.session_state.uploaded_data["WalkingSpeed"]
            walking_length = st.session_state.uploaded_data["WalkingStepLength"]
            speed_sources = walking_speed["sourceName"].dropna().unique().tolist()
            length_sources = walking_length["sourceName"].dropna().unique().tolist()
            st.session_state["walking_speed"] = walking_speed
            all_sources = list(set(speed_sources + length_sources))

            col1, col2 = st.columns(2)

            with col1:
                selected_sources = st.multiselect(
                    "Kaynak Seç",
                    options=all_sources,
                    default=all_sources,
                    key = "wl_selected_sources"
                )
            with col2:
                view_mode = st.selectbox(
                    "Grafik Tipi Seç",
                    ["Günlük Yürüme Hızı", "Haftanın Gününe Göre Hız",
                     "Zamana Dayalı Adım Uzunluğu"],
                    key="wl_view_mode"
                )
            filtered_speed = walking_speed[walking_speed["sourceName"].isin(st.session_state.wl_selected_sources)]
            filtered_length = walking_length[walking_length["sourceName"].isin(st.session_state.wl_selected_sources)]

            if st.session_state.wl_view_mode == "Günlük Yürüme Hızı":
                grouped = get_metric_grouped(filtered_speed, "date")
                plot_speed_daily(grouped)
                avg_speed = (
                    filtered_speed.groupby("sourceName")["value"]
                    .mean()
                    .reset_index()
                    .rename(columns={"value": "Ortalama Hız (km/h)", "sourceName": "Kaynak"})
                    .sort_values("Ortalama Hız (km/h)", ascending=False)
                )
                st.dataframe(avg_speed, use_container_width=True)
            elif st.session_state.wl_view_mode == "Haftanın Gününe Göre Hız":
                grouped = get_metric_grouped(filtered_speed, "dow")
                plot_speed_by_dow(grouped)
            elif st.session_state.wl_view_mode == "Zamana Dayalı Adım Uzunluğu":
                grouped = get_metric_grouped(filtered_length, "date")
                plot_step_length_daily(grouped)
                avg_length = (
                    walking_length.groupby("sourceName")["value"]
                    .mean()
                    .reset_index()
                    .rename(columns={"sourceName": "Kaynak", "value": "Ortalama Adım Uzunluğu (cm)"})
                    .sort_values("Ortalama Adım Uzunluğu (cm)", ascending=False)
                )

                st.dataframe(avg_length, use_container_width=True)

with tab3:
    sub_tab1, sub_tab2, sub_tab3, sub_tab4, sub_tab5, sub_tab6,sub_tab7  = st.tabs([
        "Nabız",
        "Kilo & Boy",
        "Kalori",
        "VO2Max",
        "HRV",
        "Solunum",
        "Yürüyüş Kalp Yükü"
    ])
    with sub_tab1:
        if "HeartRate" in st.session_state.uploaded_data:
            heart_rate = st.session_state.uploaded_data["HeartRate"]
            source_options = heart_rate["sourceName"].dropna().unique().tolist()
            selected_sources = st.multiselect(
                "Kaynak Seç (Nabız)",
                options=source_options,
                default=source_options,
                key = "hr_selected_sources"
            )
            filtered = heart_rate[heart_rate["sourceName"].isin(st.session_state.hr_selected_sources)]
            grouped = get_heart_rate_grouped(filtered)
            plot_heart_rate_daily(grouped)
    with sub_tab2:
        if "BodyMass" in st.session_state.uploaded_data:
            body_mass = st.session_state.uploaded_data["BodyMass"]
            body_mass["BMI"] = body_mass["value"] / ((height / 100) ** 2)
            col1, col2 = st.columns(2)
            with col1:
                source_options = body_mass["sourceName"].dropna().unique().tolist()
                selected_sources = st.multiselect(
                    "Kaynak Seç (Kilo)", options=source_options, default=source_options,
                key = "bm_sources"
                )

            with col2:
                view_mode = st.selectbox(
                    "Görünüm Seç", ["Aylık Kilo", "BMI"],
                key = "bm_view_mode"
                )

            filtered = body_mass[body_mass["sourceName"].isin(st.session_state.bm_sources)]

            if st.session_state.bm_view_mode == "Aylık Kilo":
                grouped = get_weight_monthly_avg(filtered)
                plot_weight_by_month(grouped)
            elif st.session_state.bm_view_mode == "BMI":
                bmi_df = calculate_bmi(filtered, height)
                plot_bmi_line(bmi_df)
    with sub_tab3:
        if "ActiveEnergyBurned" in st.session_state.uploaded_data and "BasalEnergyBurned" in st.session_state.uploaded_data:
            active_df = st.session_state.uploaded_data["ActiveEnergyBurned"]
            basal_df = st.session_state.uploaded_data["BasalEnergyBurned"]
            sources = sorted(
                list(set(active_df["sourceName"].dropna().unique()) | set(basal_df["sourceName"].dropna().unique()))
            )
            col1, col2 = st.columns([1, 1])

            with col1:
                selected_sources = st.multiselect("Kaynak Seç",
                                                  options=sources,
                                                  default=sources,
                                                  key = "energy_selected_sources")

            with col2:
                view_mode = st.selectbox(
                    "Görünüm Seç",
                    ["Toplam Kalori (Günlük)", "Haftanın Günlerine Göre Aktif Kalori"],
                    key = "energy_view_mode"
                )
            active_filtered = active_df[active_df["sourceName"].isin(st.session_state.energy_selected_sources)]
            basal_filtered = basal_df[basal_df["sourceName"].isin(st.session_state.energy_selected_sources)]
            if st.session_state.energy_view_mode == "Toplam Kalori (Günlük)":
                combined = get_daily_total_energy(active_filtered, basal_filtered)
                plot_daily_total_energy(combined)
            elif st.session_state.energy_view_mode == "Haftanın Günlerine Göre Aktif Kalori":
                grouped = get_active_energy_by_dow(active_filtered)
                plot_active_energy_by_dow(grouped)
    with sub_tab4:
        if "VO2Max" in st.session_state.uploaded_data:
            vo2max= st.session_state.uploaded_data["VO2Max"]
            plot_vo2max(vo2max)
        else:
            st.info("VO2Max verisi yüklenmemiştir.")

    with sub_tab5:
        if "HeartRateVariabilitySDNN" in st.session_state.uploaded_data:
            hrv = st.session_state.uploaded_data["HeartRateVariabilitySDNN"]
            plot_single_metric(hrv, "HRV Zaman Serisi", "HRV")
        else:
            st.info("HRV verisi yüklenmemiştir.")

    with sub_tab6:
        if "OxygenSaturation" in st.session_state.uploaded_data and "RespiratoryRate" in st.session_state.uploaded_data:
            spo2 = st.session_state.uploaded_data["OxygenSaturation"]
            respiratory = st.session_state.uploaded_data["RespiratoryRate"]
            plot_single_metric(spo2, "SpO2 Zaman Serisi", "SpO2")
            plot_single_metric(respiratory, "Solunum Hızı Zaman Serisi", "Solunum Hızı")
        else:
            st.info("SpO2 veya Solunum Hızı verisi yüklenmemiştir.")

    with sub_tab7:
        if "WalkingHeartRateAverage" in st.session_state.uploaded_data:
            walking_hr = st.session_state.uploaded_data["WalkingHeartRateAverage"]
            plot_single_metric(walking_hr, "Yürüyüş Nabzı Ortalaması", "Yürüyüş HR")
        else:
            st.info("WalkingHeartRateAverage verisi yüklenmemiştir.")

        if "RestingHeartRate" in st.session_state.uploaded_data:
            resting_hr = st.session_state.uploaded_data["RestingHeartRate"]
            plot_single_metric(resting_hr, "Dinlenik Nabız Zaman Serisi", "Resting HR")
        else:
            st.info("RestingHeartRate verisi yüklenmemiştir.")

        if "HeartRateRecoveryOneMinute" in st.session_state.uploaded_data:
            hr_recovery = st.session_state.uploaded_data["HeartRateRecoveryOneMinute"]
            plot_single_metric(hr_recovery, "Egzersiz Sonrası Toparlanma",
                               "HR Recovery")
        else:
            st.info("HeartRateRecoveryOneMinute verisi yüklenmemiştir.")
with tab4:
        if "SleepAnalysis" in st.session_state.uploaded_data:
            sleep_df = st.session_state.uploaded_data["SleepAnalysis"]
            sleep_df["value"] = sleep_df["sleep_duration_hours"]
            source_options = sleep_df["sourceName"].dropna().unique().tolist()
            col1, col2 = st.columns(2)
            with col1:
                selected_sources = st.multiselect(
                    "Kaynak Seçiniz",
                    options=source_options,
                    default=source_options,
                    key = "sleep_sources"
                )
            with col2:
                view_option = st.selectbox(
                    "Görünüm Seçiniz",
                    ["Haftalık Ortalama Uyuma Saatleri", "Uyku Tipine Göre Dağılım"],
                    key = "sleep_view"
                )

            filtered_df = sleep_df[sleep_df["sourceName"].isin(st.session_state.sleep_sources)]
            avg_by_dow, sleep_type_dist = get_sleep_metrics(filtered_df)

            if st.session_state.sleep_view == "Haftalık Ortalama Uyuma Saatleri":
                plot_avg_sleep_by_dow(avg_by_dow)
            elif st.session_state.sleep_view == "Uyku Tipine Göre Dağılım":
                plot_sleep_type_pie(sleep_type_dist)


with tab5:
    active_df = st.session_state.uploaded_data.get("ActiveEnergyBurned")
    basal_df = st.session_state.uploaded_data.get("BasalEnergyBurned")

    if active_df is not None and basal_df is not None:
        active_df = active_df.copy()
        basal_df = basal_df.copy()

        active_df = active_df[active_df["sourceName"] == "Ali Haydar’s Apple Watch"]
        basal_df = basal_df[basal_df["sourceName"] == "Ali Haydar’s Apple Watch"]

        active_df["startDate"] = pd.to_datetime(active_df["startDate"]).dt.floor("D")
        basal_df["startDate"] = pd.to_datetime(basal_df["startDate"]).dt.floor("D")

        total_df = pd.merge(
            active_df.groupby("startDate")["value"].sum().reset_index(name="active"),
            basal_df.groupby("startDate")["value"].sum().reset_index(name="basal"),
            on="startDate",
            how="outer"
        )
        total_df["value"] = total_df["active"].fillna(0) + total_df["basal"].fillna(0)
        total_df["date"] = total_df["startDate"]
    else:
        total_df = None
    step_df = st.session_state.get("StepCount")
    if step_df is not None:
        step_df = step_df[step_df["sourceName"] == "Ali Haydar Akca’s iPhone"]
        st.session_state["step_count_filtered"] = step_df
    heart_rate_df = st.session_state.uploaded_data.get("HeartRate")
    if heart_rate_df is not None:
        heart_rate_df = heart_rate_df[heart_rate_df["sourceName"] == "Ali Haydar’s Apple Watch"]
        st.session_state["heart_rate_filtered"] = heart_rate_df
    dwr_df = st.session_state.uploaded_data.get("DistanceWalkingRunner")
    if dwr_df is not None:
        dwr_df = dwr_df[dwr_df["sourceName"] == "Ali Haydar Akca’s iPhone"]
        st.session_state["distance_walking_filtered"] = dwr_df
    ws_df = st.session_state.uploaded_data.get("WalkingSpeed")
    if ws_df is not None:
        ws_df = ws_df[ws_df["sourceName"] == "Ali Haydar Akca’s iPhone"]
        st.session_state["walking_speed_filtered"] = ws_df
    sleep_df = st.session_state.uploaded_data.get("SleepAnalysis")
    if sleep_df is not None:
        sleep_df = sleep_df[sleep_df["sourceName"] == "Ali Haydar Akca’s iPhone"]
        st.session_state["sleep_df_filtered"] = sleep_df
    spo2_df = st.session_state.uploaded_data.get("OxygenSaturation")
    if spo2_df is not None:
        spo2_df = spo2_df[spo2_df["sourceName"] == "Ali Haydar’s Apple Watch"]
        st.session_state["spo2_df_filtered"] = spo2_df
    available_metrics = {
        "Adım Sayısı": st.session_state.get("step_count", step_df),
        "Yürünen Mesafe": st.session_state.get("distance_walking_runner", dwr_df),
        "Yürüme Hızı": st.session_state.get("walking_speed", ws_df),
        "Aktif Enerji (kcal)": active_df,
        "Bazal Enerji (kcal)": basal_df,
        "Toplam Enerji (kcal)": total_df,
        "Uyku Süresi (saat)": st.session_state.get("sleep_analysis", sleep_df),
        "Nabız": st.session_state.uploaded_data.get("HeartRate", heart_rate_df),
        "VO2Max": st.session_state.uploaded_data.get("VO2Max"),
        "HRV": st.session_state.uploaded_data.get("HeartRateVariabilitySDNN"),
        "SpO2": st.session_state.uploaded_data.get("OxygenSaturation", spo2_df),
        "Solunum Hızı (RespiratoryRate)": st.session_state.uploaded_data.get("RespiratoryRate"),
        "Yürüyüş Nabzı (WalkingHeartRateAverage)": st.session_state.uploaded_data.get("WalkingHeartRateAverage"),
        "Dinlenik Nabız (RestingHeartRate)": st.session_state.uploaded_data.get("RestingHeartRate"),
        "Egzersiz Sonrası Toparlanma (Kalp Atış Toparlanması)": st.session_state.uploaded_data.get("HeartRateRecoveryOneMinute")
    }

    selected_vars = st.multiselect(
        "İncelenecek Değişkenler (en az 2 adet seçiniz)",
        options=[k for k, v in available_metrics.items() if v is not None],
        default=["Nabız", "Adım Sayısı"],
        key="correlation_multiselect"
    )


    if len(selected_vars) >= 2:
        merged = None
        for var in selected_vars:
            df = available_metrics[var]
            if df is None:
                continue
            df = df.copy()
            df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.tz_localize(None).dt.floor("D")
            df_grouped = df.groupby("date")["value"].mean().reset_index(name=var)

            if merged is None:
                merged = df_grouped
            else:
                merged = pd.merge(merged, df_grouped, on="date", how="inner")

        if merged is not None and not merged.empty:
            # Eğer sadece 2 değişken varsa korelasyon hesapla ve çift eksenli çiz
            if len(selected_vars) == 2:
                corr = merged[selected_vars[0]].corr(merged[selected_vars[1]])
                st.metric("Korelasyon (r)", f"{corr:.2f}")

                fig = go.Figure()
                fig.add_trace(go.Scatter(x=merged["date"], y=merged[selected_vars[0]], name=selected_vars[0], yaxis="y1"))
                fig.add_trace(go.Scatter(x=merged["date"], y=merged[selected_vars[1]], name=selected_vars[1], yaxis="y2"))

                fig.update_layout(
                    title=f"{selected_vars[0]} ve {selected_vars[1]} Zaman Serisi",
                    xaxis=dict(title="Tarih"),
                    yaxis=dict(title=selected_vars[0], side="left"),
                    yaxis2=dict(title=selected_vars[1], overlaying="y", side="right"),
                    legend=dict(x=0.5, y=1.1, orientation="h"),
                    hovermode="x unified"
                )
                st.plotly_chart(fig, use_container_width=True)

            else:
                st.subheader("Zaman Serisi Karşılaştırma")

                fig = go.Figure()
                for var in selected_vars:
                    fig.add_trace(go.Scatter(x=merged["date"], y=merged[var], name=var))

                fig.update_layout(
                    xaxis=dict(title="Tarih"),
                    yaxis=dict(title="Değer"),
                    legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center"),
                    hovermode="x unified"
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Seçilen değişkenler için ortak tarihli veri bulunamadı.")

