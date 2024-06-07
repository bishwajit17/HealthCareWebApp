from django import template

register = template.Library()

@register.filter(name='add_currency_symbol')
def add_currency_symbol(cost, currency_symbol='£'):
    return f'{currency_symbol}{cost}'