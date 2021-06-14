# Functions related to detecting ecommerce software on websites

from bs4 import BeautifulSoup


def detect_cart_softwares(html):
    """
    The commented-out detectors are old versions that worked very well, but 
    not quite as well as their replacement.
    
    Does not handle custom/manually-implemented cart software.
    """
    bs = BeautifulSoup(html, 'html.parser')
    detected_carts = []
        
    # Demandware is a subsidiary of Salesforce and was renamed to Salesforce Commerce Cloud
    if any('demandware' in tag['src'] for tag in bs.find_all('img', {'src': True})):
        detected_carts.append('Demandware')
        
    if bs.find('script', attrs={'type': 'text/x-magento-init'}) is not None:
        detected_carts.append('Magento')
        
    if bs.find('span', attrs={'class': 'nosto_cart'}) is not None:
        detected_carts.append('nosto')
        
#     if any('var Shopify =' in script.string for script in bs.find_all('script') if script.string]):
#         detected_carts.append('Shopify')
    if any('shopify' in tag['href'] for tag in bs.find_all('link', {'rel': 'stylesheet', 'href': True})):
        detected_carts.append('Shopify')
        
    sitecore_detector = any('sitecore-link-wrapper' in tag['class'] for tag in bs.find_all('div', {'class': True}))
    if sitecore_detector or 'SITECORE_APIKEY' in str(bs):
        detected_carts.append('Sitecore Experience Commerce')
        
    if bs.find('link', {'rel': 'preconnect', 'href': 'https://images.squarespace-cdn.com'}) is not None:
        detected_carts.append('Squarespace')
        
    # These two Wix detections work perfectly/identically on the testing websites, so I left just the computationally cheapest
    if bs.find('meta', {'name': 'generator', 'content': 'Wix.com Website Builder'}) is not None:
        detected_carts.append('Wix Stores')
#     elif any('static.parastorage.com' in tag['src'] for tag in bs.find_all('script', {'src': True})):
#         detected_carts.append('Wix Stores')
        
#     woocommerce_script_detector = ['woocommerce' in tag['src'] for tag in bs.find_all('script', {'src': True})]
#     if True in woocommerce_script_detector:
#         detected_carts.append('WooCommerce')
#     woocommerce_link_detector = ['woocommerce' in tag['id'] for tag in bs.find_all('link', {'rel': 'stylesheet', 'id': True})]
#     if True in woocommerce_link_detector:
#         detected_carts.append('WooCommerce')
    if bs.find('style', {'id': 'woocommerce-inline-inline-css', 'type': 'text/css'}) is not None:
        detected_carts.append('WooCommerce')
        
    return detected_carts


def detect_if_has_card(html):
    bs = BeautifulSoup(html, 'html.parser')
    
    if 'addtocart' in html.lower():
        return True
    elif any(tag['href'] for tag in bs.find_all('a', {'href': True}) if 'payment' in tag['href']):
        return True
    elif any('payment' in tag_class for tag in bs.find_all('li', {'class': True}) for tag_class in tag['class']):
        return True
    
    return False


def detect_payment_systems(html):
    payment_names = ['visa','mastercard','amex','applepay','afterpay','zippay',
                     'alipay','klarna']
    
    html_lower = html.lower()
    detected_cards = [
        payment_name for payment_name in payment_names
        if payment_name in html_lower
    ]
    
    return detected_cards