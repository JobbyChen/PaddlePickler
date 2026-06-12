import csv
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote_plus

import streamlit as st


CSV_FILENAME = "paddles_balanced_90_real_links.csv"


@dataclass
class Paddle:
    name: str
    price: float
    styles: list
    skill_fit: list
    weight_oz: float
    handle_length: float
    thickness_mm: int
    power: int
    control: int
    spin: int
    forgiveness: int
    notes: str
    image_url: str = ""
    buy_url: str = ""
    image_search_url: str = ""
    handle_category: str = ""
    weight_category: str = ""
    price_category: str = ""


def safe_get(row, column_name, default=""):
    if column_name in row and row[column_name] is not None:
        return row[column_name].strip()
    return default


def infer_handle_category(handle_length):
    if handle_length <= 5.3:
        return "short"
    if handle_length >= 5.6:
        return "long"
    return "standard"


def infer_weight_category(weight_oz):
    if weight_oz < 7.9:
        return "light"
    if weight_oz > 8.15:
        return "heavy"
    return "medium"


def infer_price_category(price):
    if price <= 120:
        return "budget"
    if price <= 220:
        return "mid-range"
    return "premium"


def load_paddles_from_csv(filename):
    paddles = []

    with open(filename, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            price = float(row["price"])
            weight_oz = float(row["weight_oz"])
            handle_length = float(row["handle_length"])

            paddles.append(
                Paddle(
                    name=row["name"],
                    price=price,
                    styles=row["styles"].split("|"),
                    skill_fit=row["skill_fit"].split("|"),
                    weight_oz=weight_oz,
                    handle_length=handle_length,
                    thickness_mm=int(row["thickness_mm"]),
                    power=int(row["power"]),
                    control=int(row["control"]),
                    spin=int(row["spin"]),
                    forgiveness=int(row["forgiveness"]),
                    notes=row["notes"],
                    image_url=safe_get(row, "image_url"),
                    buy_url=safe_get(row, "buy_url"),
                    image_search_url=safe_get(row, "image_search_url"),
                    handle_category=safe_get(row, "handle_category", infer_handle_category(handle_length)),
                    weight_category=safe_get(row, "weight_category", infer_weight_category(weight_oz)),
                    price_category=safe_get(row, "price_category", infer_price_category(price)),
                )
            )

    return paddles


def handle_target(preference):
    if preference == "Short":
        return 5.25
    if preference == "Long":
        return 5.75
    return 5.5


def weight_target(preference):
    if preference == "Light":
        return 7.7
    if preference == "Heavy":
        return 8.3
    return 8.0


def score_paddle(paddle, user):
    score = 0

    score += paddle.control * user["control_importance"]
    score += paddle.power * user["power_importance"]
    score += paddle.spin * user["spin_importance"]
    score += paddle.forgiveness * user["forgiveness_importance"]

    if user["skill"] in paddle.skill_fit:
        score += 25
    elif user["skill"] == "beginner" and "advanced" in paddle.skill_fit:
        score -= 25
    else:
        score -= 5

    if user["play_style"] in paddle.styles:
        score += 20

    if user["budget_style"] == "budget":
        if paddle.price <= 120:
            score += 20
        elif paddle.price > 200:
            score -= 15

    if paddle.price > user["budget"]:
        score -= (paddle.price - user["budget"]) * 0.35

    score -= abs(paddle.handle_length - handle_target(user["handle"])) * 20
    score -= abs(paddle.weight_oz - weight_target(user["weight"])) * 15

    if user["skill"] == "beginner":
        score += paddle.forgiveness * 2
        score += paddle.control * 1.5
        score -= paddle.power * 0.5
    elif user["skill"] == "advanced":
        score += paddle.power
        score += paddle.spin

    return round(score, 2)


def apply_filters(paddles, filter_handle, filter_weight, filter_price, filter_style):
    filtered = paddles

    if filter_handle != "Any":
        filtered = [p for p in filtered if p.handle_category == filter_handle.lower()]

    if filter_weight != "Any":
        filtered = [p for p in filtered if p.weight_category == filter_weight.lower()]

    if filter_price != "Any":
        filtered = [p for p in filtered if p.price_category == filter_price.lower()]

    if filter_style != "Any":
        filtered = [p for p in filtered if filter_style.lower() in p.styles]

    return filtered


def recommend_paddles(user, paddles, top_n):
    scored = [(score_paddle(paddle, user), paddle) for paddle in paddles]
    scored.sort(reverse=True, key=lambda item: item[0])
    return scored[:top_n]


def explain_match(paddle, user):
    reasons = []

    if user["skill"] in paddle.skill_fit:
        reasons.append(f"fits your {user['skill']} skill level")

    if user["play_style"] in paddle.styles:
        reasons.append(f"matches your {user['play_style']} play style")

    if paddle.price <= user["budget"]:
        reasons.append("is within your budget")
    else:
        reasons.append("is over your budget")

    if user["control_importance"] >= 4 and paddle.control >= 8:
        reasons.append("has strong control")

    if user["power_importance"] >= 4 and paddle.power >= 8:
        reasons.append("has strong power")

    if user["spin_importance"] >= 4 and paddle.spin >= 8:
        reasons.append("has strong spin")

    if user["forgiveness_importance"] >= 4 and paddle.forgiveness >= 8:
        reasons.append("has a forgiving sweet spot")

    if not reasons:
        return "This is a balanced option based on your answers."

    return "This paddle " + ", ".join(reasons) + "."


def show_rating(label, value):
    st.write(f"**{label}:** {value}/10")
    st.progress(value / 10)


def get_buy_link(paddle):
    if paddle.buy_url:
        return paddle.buy_url
    search_query = quote_plus(paddle.name + " pickleball paddle buy")
    return f"https://www.pickleballwarehouse.com/searchresults.html?searchtext={search_query}"


def get_image_search_link(paddle):
    if paddle.image_search_url:
        return paddle.image_search_url
    search_query = quote_plus(paddle.name + " pickleball paddle image")
    return f"https://www.google.com/search?tbm=isch&q={search_query}"


def main():
    st.set_page_config(
        page_title="Paddle Picker",
        page_icon="🏓",
        layout="wide"
    )

    st.title("🏓 Paddle Picker")
    st.write(
        "Find a pickleball paddle based on skill level, play style, budget, handle length, "
        "weight, and performance priorities."
    )

    if not Path(CSV_FILENAME).exists():
        st.error(f"Could not find {CSV_FILENAME}. Make sure it is uploaded with app.py.")
        return

    paddles = load_paddles_from_csv(CSV_FILENAME)

    st.sidebar.header("Your Preferences")

    skill_display = st.sidebar.selectbox("Skill level", ["Beginner", "Intermediate", "Advanced"])
    play_style_display = st.sidebar.selectbox(
        "Preferred play style",
        ["Control", "Power", "Spin", "All-court", "Singles", "Doubles"]
    )
    handle = st.sidebar.selectbox("Preferred handle length", ["Short", "Standard", "Long"])
    weight = st.sidebar.selectbox("Preferred paddle weight", ["Light", "Medium", "Heavy"])
    budget_style_display = st.sidebar.radio("Budget preference", ["Budget", "Any"])
    budget = st.sidebar.slider("Maximum budget", min_value=50, max_value=350, value=200, step=10)

    st.sidebar.subheader("Trait Importance")
    control = st.sidebar.slider("Control", 1, 5, 4)
    power = st.sidebar.slider("Power", 1, 5, 3)
    spin = st.sidebar.slider("Spin", 1, 5, 4)
    forgiveness = st.sidebar.slider("Forgiveness", 1, 5, 4)

    st.sidebar.subheader("Optional Hard Filters")
    filter_handle = st.sidebar.selectbox("Only show handle category", ["Any", "Short", "Standard", "Long"])
    filter_weight = st.sidebar.selectbox("Only show weight category", ["Any", "Light", "Medium", "Heavy"])
    filter_price = st.sidebar.selectbox("Only show price category", ["Any", "Budget", "Mid-range", "Premium"])
    filter_style = st.sidebar.selectbox(
        "Only show style category",
        ["Any", "Control", "Power", "Spin", "All-court", "Singles", "Doubles", "Budget"]
    )

    top_n = st.sidebar.slider("Number of recommendations", 3, 10, 5)

    user = {
        "skill": skill_display.lower(),
        "play_style": play_style_display.lower(),
        "handle": handle,
        "weight": weight,
        "budget_style": budget_style_display.lower(),
        "budget": budget,
        "control_importance": control,
        "power_importance": power,
        "spin_importance": spin,
        "forgiveness_importance": forgiveness,
    }

    filtered_paddles = apply_filters(paddles, filter_handle, filter_weight, filter_price, filter_style)

    st.caption(
        f"Dataset: {len(paddles)} paddles. Current filters show {len(filtered_paddles)} paddles. "
        "Ratings are normalized for this recommender."
    )

    if len(filtered_paddles) == 0:
        st.warning("No paddles match those hard filters. Try changing one filter to Any.")
        return

    recommendations = recommend_paddles(user, filtered_paddles, top_n)

    st.subheader("Your Best Matches")

    for index, item in enumerate(recommendations, start=1):
        score, paddle = item

        st.divider()
        left_col, right_col = st.columns([1, 2])

        with left_col:
            if paddle.image_url:
                st.image(paddle.image_url, use_container_width=True)
            else:
                st.info("No paddle image yet")
                st.markdown("## 🏓")

        with right_col:
            st.subheader(f"#{index} Match: {paddle.name}")

            score_percent = min(max(score / 250, 0), 1)
            st.write(f"**Match Score:** {score}")
            st.progress(score_percent)

            spec_col1, spec_col2, spec_col3, spec_col4 = st.columns(4)
            spec_col1.metric("Price", f"${paddle.price:.2f}")
            spec_col2.metric("Weight", f"{paddle.weight_oz} oz")
            spec_col3.metric("Handle", f'{paddle.handle_length}"')
            spec_col4.metric("Thickness", f"{paddle.thickness_mm} mm")

            st.write(
                f"**Categories:** {paddle.handle_category} handle, "
                f"{paddle.weight_category} weight, {paddle.price_category} price"
            )

            if paddle.price <= budget:
                st.success("Within budget")
            else:
                st.warning("Over budget")

            st.write("**Style Tags:** " + ", ".join(paddle.styles))
            st.write("**Skill Fit:** " + ", ".join(paddle.skill_fit))

            button_col1, button_col2 = st.columns(2)
            button_col1.link_button("View / Buy Paddle", get_buy_link(paddle))
            button_col2.link_button("Find Real Images", get_image_search_link(paddle))

            with st.expander("See performance details"):
                rating_col1, rating_col2 = st.columns(2)
                with rating_col1:
                    show_rating("Power", paddle.power)
                    show_rating("Control", paddle.control)
                with rating_col2:
                    show_rating("Spin", paddle.spin)
                    show_rating("Forgiveness", paddle.forgiveness)

            st.write("**Why this matches you:**")
            st.write(explain_match(paddle, user))

            st.write("**Notes:**")
            st.write(paddle.notes)


if __name__ == "__main__":
    main()
