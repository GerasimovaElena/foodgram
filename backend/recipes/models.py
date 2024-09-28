import random

from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

from .constants import CHARACTERS, SHORT_LINK_LENGTH, STRING_LENGTH_LIMIT

User = get_user_model()


class Tag(models.Model):
    name = models.CharField('Название', max_length=32)
    slug = models.SlugField(max_length=32, unique=True)

    class Meta:
        verbose_name = 'Teг'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        'Название',
        max_length=128,
        unique=True
    )
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=64,
        default='г'
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f'{self.name[:STRING_LENGTH_LIMIT]}, {self.measurement_unit}'


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='recipes'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты',
        related_name='recipes'
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Тег',
        related_name='recipes'
    )
    image = models.ImageField(
        'Картинка',
        upload_to='recipes/'
    )
    name = models.CharField(
        'Название',
        max_length=256
    )
    text = models.TextField('Текстовое описание')
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления',
        validators=[MinValueValidator(1)]
    )
    pub_date = models.DateTimeField(
        'Дата публикации рецепта',
        auto_now_add=True
    )
    short_link = models.CharField(
        'Короткая ссылка',
        max_length=SHORT_LINK_LENGTH,
        unique=True
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.name[:STRING_LENGTH_LIMIT]

    def save(self, *args, **kwargs):
        if not self.short_link:
            self.short_link = self.generate_short_link()
        super().save(*args, **kwargs)

    def generate_short_link(self):
        while True:
            short_link = ''.join(
                random.choice(CHARACTERS) for _ in range(SHORT_LINK_LENGTH)
            )
            if not Recipe.objects.filter(short_link=short_link).exists():
                return short_link


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент'
    )
    amount = models.PositiveIntegerField(
        'Кол-во',
        validators=[MinValueValidator(1)]
    )

    class Meta:
        verbose_name = 'Рецепт-Ингредиент'
        verbose_name_plural = 'Рецепт-Ингредиент'


class UserRecipeRelation(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='%(class)s'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='%(class)s'
    )

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_user_recipe'
            )
        ]


class Favorite(UserRecipeRelation):
    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'


class ShoppingCart(UserRecipeRelation):
    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
