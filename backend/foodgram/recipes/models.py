from django.contrib.auth import get_user_model
from django.db import models


User = get_user_model()

class Tag(models.Model):
    name = models.CharField(max_length=32)
    slug = models.SlugField(
        max_length=32,
        unique=True,
        null=True,
        blank=True
    )

    def __str__(self):
        return self.name

class Ingredient(models.Model):
    name = models.CharField(max_length=100, unique=True)
    unit = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.name} ({self.unit})"
    
  
class Recipe(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)  # Автор рецепта
    title = models.CharField(max_length=200)  # Название рецепта
    image = models.ImageField(upload_to='recipes/')  # Картинка рецепта
    description = models.TextField()  # Текстовое описание рецепта
    ingredients = models.ManyToManyField(
        Ingredient, 
        through='RecipeIngredient',  # Через вспомогательную модель
        related_name='recipes'
    )  # Ингредиенты для рецепта
    tags = models.ManyToManyField(Tag, related_name='recipes')  # Теги
    cooking_time = models.PositiveIntegerField()  # Время приготовления в минутах

    def __str__(self):
        return self.title

# Вспомогательная модель для указания количества ингредиентов в рецепте
class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    quantity = models.FloatField()  # Количество ингредиента
    unit = models.CharField(max_length=50)  # Единица измерения

    def __str__(self):
        return f"{self.quantity} {self.unit} {self.ingredient.name} для {self.recipe.title}"