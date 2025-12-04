import torch
import torch.nn as nn

class SimpleModel(nn.Module):
    def __init__(self):
        super(SimpleModel, self).__init__()
        self.fc = nn.Linear(10, 5)
        
    def forward(self):
        # Генерируем случайные данные для демонстрации
        x = torch.randn(1, 10)
        return self.fc(x)


model = SimpleModel()

# Или через scripting
scripted_model = torch.jit.script(model)
scripted_model.save("model.pt")
print('Done')
