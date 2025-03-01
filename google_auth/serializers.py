from rest_framework import serializers

class GoogleAuthSerializer(serializers.Serializer):
    id_token = serializers.CharField(required=True)

    def validate(self, attrs):
        id_token = attrs.get("id_token")
        if not id_token:
            raise serializers.ValidationError("ID Token is required.")

        attrs["id_token"] = id_token
        return attrs