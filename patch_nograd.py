with open('web.py', 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace(
    'background: linear-gradient(135deg, #f79533, #f37055, #ef4e7b, #a166ab, #5073b8);',
    'background: #2c2c2e;'
)
c = c.replace(
    'background: linear-gradient(135deg, #3b82f6, #8b5cf6);',
    'background: #3b82f6;'
)
c = c.replace(
    'box-shadow: 0 4px 20px rgba(239,78,123,0.4);',
    ''
)
c = c.replace(
    'box-shadow: 0 4px 15px rgba(59,130,246,0.4);',
    ''
)

with open('web.py', 'w', encoding='utf-8') as f:
    f.write(c)
print('Gradients removed.')
