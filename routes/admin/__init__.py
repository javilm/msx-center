# Top admin page
from page_admin import page_admin

# Articles
from page_admin_articles import page_admin_articles

# Article categories
from page_admin_categories import page_admin_categories
from page_admin_categories_add import page_admin_categories_add
from page_admin_categories_edit import page_admin_categories_edit

# Lounges
from page_admin_lounges import page_admin_lounges
from page_admin_lounges_add import page_admin_lounges_add
from page_admin_lounges_edit import page_admin_lounges_edit

# Members
from page_admin_members import page_admin_members
# There is no page_admin_members_add because new members are supposed to sign
# up via the signup form
from page_admin_members_edit import page_admin_members_edit

# External links
from page_admin_links import page_admin_links
from page_admin_links_add import page_admin_links_add
from page_admin_links_edit import page_admin_links_edit

# News
from page_admin_news import page_admin_news
from page_admin_news_add import page_admin_news_add
from page_admin_news_edit import page_admin_news_edit

# Domains
from page_admin_domains import page_admin_domains

# AJAX backend code
from ajax_admin_news_add_feature_image import ajax_admin_news_add_feature_image
from ajax_admin_link_info import ajax_admin_link_info

__all__ = [
	"page_admin",
	"page_admin_articles",
	"page_admin_categories",
	"page_admin_categories_add",
	"page_admin_categories_edit",
	"page_admin_lounges",
	"page_admin_lounges_add",
	"page_admin_lounges_edit",
	"page_admin_members",
	"page_admin_members_edit",
	"page_admin_links",
	"page_admin_links_add",
	"page_admin_links_edit",	
	"page_admin_news",
	"page_admin_news_add",
	"page_admin_news_edit",
	"page_admin_domains",
	"ajax_admin_news_add_feature_image",
	"ajax_admin_link_info"
]