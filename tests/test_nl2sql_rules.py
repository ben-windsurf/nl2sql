from app.nl2sql import rule_based

def test_top_products():
    sql = rule_based("Show me the top 3 products by revenue", {})
    assert "FROM order_items" in sql and "ORDER BY revenue DESC" in sql

def test_count_orders_last_month():
    sql = rule_based("How many orders did we get last month?", {})
    assert "COUNT" in sql and "FROM orders" in sql

def test_revenue_by_month():
    sql = rule_based("List total revenue by month for 2024.", {})
    assert "strftime('%Y-%m'" in sql and "GROUP BY ym" in sql
