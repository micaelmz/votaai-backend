from rest_framework import status
from rest_framework.response import Response
from rest_framework import viewsets
from app.serializers.user_serializer import UserSerializer
from app.services.user_service import UserService
from app.services.email_service import EmailService
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import permission_classes, action


class UserViewSet(viewsets.ViewSet):
    _service = UserService()

    def get_permissions(self):
        if self.action in ['list', 'create']:
            self.permission_classes = [AllowAny]
        else:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    # GET
    def list(self, request):
        users = self._service.get_all_users()
        if users['success']:
            return Response(users['data'], status=status.HTTP_200_OK)
        return Response({'error': users['error']}, status=status.HTTP_404_NOT_FOUND)

    # GET
    def retrieve(self, request, pk=None):
        # TODO: BUG - se tiver um ponto no pk ele da um erro
        if not pk:
            return Response({'error': 'Missing parameter'}, status=status.HTTP_400_BAD_REQUEST)

        if str(pk).isdigit():
            if len(str(pk)) == 11:
                user = self._service.get_user_by_cpf(pk)
            else:
                user = self._service.get_user_by_id(pk)

        else:
            if '@' in str(pk):
                user = self._service.get_user_by_email(pk)
            else:
                user = self._service.get_user_by_username(pk)

        if user['success']:
            return Response(user['data'], status=status.HTTP_200_OK)

        return Response({'error': user['error']}, status=status.HTTP_404_NOT_FOUND)

    # POST
    def create(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = self._service.create_user(serializer.data)
            if user['success']:
                return Response(user['data'], status=status.HTTP_201_CREATED)
            return Response({'error': user['error']}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # PUT
    def update(self, request, pk=None):
        if not pk:
            return Response({'error': 'Missing parameter'}, status=status.HTTP_400_BAD_REQUEST)

        user = self._service.get_user_by_id(pk)
        if user['success']:
            serializer = UserSerializer(data=request.data)
            if serializer.is_valid():
                user = self._service.update_user(user['data'], serializer.data)
                if user['success']:
                    return Response(user['data'], status=status.HTTP_200_OK)
                return Response({'error': user['error']}, status=status.HTTP_400_BAD_REQUEST)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response({'error': user['error']}, status=status.HTTP_404_NOT_FOUND)

    # PATCH
    def partial_update(self, request, pk=None):
        return Response({'error': 'Not Implemented'})

    # DELETE
    def destroy(self, request, pk=None):
        return Response({'error': 'Not Implemented'})

    @action(detail=False, methods=['get'], url_path='profile')
    def get_user_to_profile(self, request):
        user_id = request.user.id
        user = self._service.get_user_by_id(user_id)

        if user['success']:
            return Response(user['data'], status=status.HTTP_200_OK)

        return Response({'error': user['error']}, status=status.HTTP_404_NOT_FOUND)


class ForgotPasswordView(viewsets.ViewSet):

    def forgot_password(self, request, email):
        _user_service = UserService()
        _email_service = EmailService()
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Missing parameter'}, status=status.HTTP_400_BAD_REQUEST)

        user = _user_service.get_user_by_email(email)['data']
        if not user:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        _email_service.send_forgot_password_email(user[0])
        return Response({'success': 'Email sent'}, status=status.HTTP_200_OK)

    def change_password(self, request):
        _user_service = UserService()
        new_password = request.data.get('new_password')
        recovery_code = request.data.get('recovery_code')

        if not new_password or not recovery_code:
            return Response({'error': 'Missing parameter'}, status=status.HTTP_400_BAD_REQUEST)

        user = _user_service.get_by_recovery_token(recovery_code)
        if not user['success']:
            return Response({'error': 'Invalid recovery code'}, status=status.HTTP_400_BAD_REQUEST)

        user = _user_service.partial_update_user(user["data"][0], {'password': new_password})

        if user['success']:
            return Response(user['data'], status=status.HTTP_200_OK)

        return Response({'error': user['error']}, status=status.HTTP_400_BAD_REQUEST)