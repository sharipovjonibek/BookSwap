
from rest_framework import serializers
from .models import Book

class BookSerializer(serializers.ModelSerializer):
    owner_username = serializers.ReadOnlyField(source="owner.username")
    image_url = serializers.SerializerMethodField(help_text="Absolute URL to the uploaded image")
    

    class Meta:
        model = Book
        fields = [
            "id","title","author","description","image","image_url",
            "phone_number","location","is_active","created_at","updated_at",
            "owner","owner_username"
        ]
        read_only_fields = ["id","created_at","updated_at","owner","owner_username","image_url"]
        extra_kwargs = {
            "location": {"help_text": "City/area for the ad.", "required": True},  # <- client must send it
        }
        extra_kwargs = {
    "title": {"help_text": "Book title (required)."},
    "author": {"help_text": "Author (optional)."},
    "description": {"help_text": "Short ad description."},
    "phone_number": {"help_text": "Owner contact phone."},
    "image": {"help_text": "Cover image upload (multipart)."},
    
    "is_active": {"help_text": "Hide/show in public list."},
}


    def get_image_url(self, obj):
        request = self.context.get("request")
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None

# ---- AI schemas for Swagger ----
class SuggestedBookSerializer(serializers.Serializer):
    title = serializers.CharField()
    author = serializers.CharField()
    why = serializers.CharField()

class AIAdvicePayloadSerializer(serializers.Serializer):
    query_intent = serializers.CharField()
    topics = serializers.ListField(child=serializers.CharField())
    suggested_books = SuggestedBookSerializer(many=True)

class FilterQuerySerializer(serializers.Serializer):
    titles = serializers.ListField(child=serializers.CharField(), required=False)
    authors = serializers.ListField(child=serializers.CharField(), required=False)

class AIAdviceResponseSerializer(serializers.Serializer):
    ai = AIAdvicePayloadSerializer()
    matched_books = BookSerializer(many=True)
    filter_query = FilterQuerySerializer()
