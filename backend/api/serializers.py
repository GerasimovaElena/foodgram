from django.contrib.auth import get_user_model
from django.db import transaction
from djoser.serializers import UserSerializer
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from rest_framework import serializers
from rest_framework.status import HTTP_400_BAD_REQUEST
from users.models import Subscription

from .mixins import Base64ImageField

User = get_user_model()


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class CustomUserSerializer(UserSerializer):
    avatar = Base64ImageField(required=False, allow_null=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )

    def get_is_subscribed(self, obj):
        current_user = self.context['request'].user
        if current_user.is_anonymous:
            return False
        return Subscription.objects.filter(
            user=current_user,
            subscribed_to=obj
        ).exists()


class SubscriptionSerializer(CustomUserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(CustomUserSerializer.Meta):
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count', 'avatar'
        )

    def get_recipes(self, obj):
        recipes_limit = (
            self.context['request'].query_params.get('recipes_limit')
        )
        if recipes_limit:
            recipes = obj.recipes.all()[:int(recipes_limit)]
        else:
            recipes = obj.recipes.all()
        return RecipeMiniSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class SubscribeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ('subscribed_to',)

    def to_representation(self, instance):
        return SubscriptionSerializer(
            instance.subscribed_to,
            context=self.context
        ).data

    def validate(self, data):
        user = self.context['request'].user
        author = data.get('subscribed_to')
        if user == author:
            raise serializers.ValidationError(
                detail='На себя подписаться нельзя',
                code=HTTP_400_BAD_REQUEST)
        return data

    def create(self, validated_data):
        user = self.context['request'].user
        author = validated_data['subscribed_to']
        if Subscription.objects.filter(
            subscribed_to=author,
            user=user
        ).exists():
            raise serializers.ValidationError(
                detail='Вы уже подписаны на этого автора',
                code=HTTP_400_BAD_REQUEST)
        return Subscription.objects.create(
            user=user,
            subscribed_to=author
        )

    def delete(self, validated_data):
        user = self.context['request'].user
        author = validated_data['subscribed_to']
        subscription = Subscription.objects.filter(
            user=user,
            subscribed_to=author
        )
        if not subscription.exists():
            raise serializers.ValidationError(
                detail='Вы не были подписаны на этого пользователя',
                code=HTTP_400_BAD_REQUEST
            )
        subscription.delete()


class UserAvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=True, allow_null=False)

    class Meta:
        model = User
        fields = ('avatar',)


class RecipeIngredientListSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeListSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientListSerializer(
        source='recipeingredient_set',
        many=True
    )
    author = CustomUserSerializer()
    tags = TagSerializer(many=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time'
        )

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        user = request.user
        if user.is_authenticated:
            return Favorite.objects.filter(user=user, recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        user = request.user
        if user.is_authenticated:
            return ShoppingCart.objects.filter(user=user, recipe=obj).exists()
        return False


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeCreateSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientCreateSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=True
    )
    author = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )
    image = Base64ImageField(required=True, allow_null=False)

    class Meta:
        model = Recipe
        fields = (
            'ingredients', 'tags', 'author',
            'image', 'name', 'text', 'cooking_time'
        )

    def to_representation(self, instance):
        return RecipeListSerializer(
            instance,
            context=self.context
        ).data

    @staticmethod
    def add_recipes_ingredients_tags(recipe, ingredients, tags):
        recipe.tags.set(tags)
        recipe_ingredients = [
            RecipeIngredient(
                ingredient=ingredient.get('id'),
                recipe=recipe,
                amount=ingredient.get('amount')
            ) for ingredient in ingredients]
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

    @transaction.atomic
    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        self.add_recipes_ingredients_tags(recipe, ingredients, tags)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        RecipeIngredient.objects.filter(recipe=instance).delete()
        self.add_recipes_ingredients_tags(instance, ingredients, tags)
        return super().update(instance, validated_data)

    def validate(self, data):
        tags = data.get('tags')
        if not tags:
            raise serializers.ValidationError(
                {'tags': 'Поле не может быть пустым'}
            )
        if list(set(tags)) != tags:
            raise serializers.ValidationError(
                {'tags': 'В поле не может быть повторений'})
        ingredients = data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError(
                {'ingredients': 'Поле не может быть пустым'}
            )
        tmp_ingredients = [ingredient.get('id') for ingredient in ingredients]
        if len(set(tmp_ingredients)) != len(tmp_ingredients):
            raise serializers.ValidationError(
                {'ingredients': 'В поле не может быть повторений'}
            )
        return data
