import re
import json
import groq
import random
import datetime
from .models import *
from .serializers import *
from django.views import View
from django.conf import settings
from django.http import JsonResponse
from django.core.mail import send_mail
from rest_framework.permissions import *
from rest_framework.views import APIView
from django.middleware.csrf import get_token
from rest_framework.response import Response
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.exceptions import PermissionDenied
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import update_last_login
from rest_framework import generics, status, views, permissions

# CSRF Token View
def get_csrf_token(request):
    return JsonResponse({'csrfToken': get_token(request)})

# Admin Registration
class AdminRegisterView(generics.CreateAPIView):
    serializer_class = AdminRegSerializer  
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            refresh = RefreshToken.for_user(user)

            user_data = {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "access_token": str(refresh.access_token),
                "refresh_token": str(refresh),
                "message": "Registration successful"
            }
            return Response(user_data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Login
class Login(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response({"message": "Email and password are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"message": "Invalid email"}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request, username=user.username, password=password)

        if not user:
            return Response({"message": "Invalid password"}, status=status.HTTP_400_BAD_REQUEST)

        if not user.is_active:
            return Response({"message": "User account is disabled"}, status=status.HTTP_400_BAD_REQUEST)

        if hasattr(user, "student_profile") and not user.student_profile.verified:
            return Response({"message": "Email not verified. Please verify your email before logging in."}, status=status.HTTP_403_FORBIDDEN)

        update_last_login(None, user)
        refresh = RefreshToken.for_user(user)

        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),
            "message": "Login successful"
        }, status=status.HTTP_200_OK)

# Generate OTP
class RequestOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"error": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Generate a 6-digit OTP
        otp = str(random.randint(100000, 999999))
        expiry_time = datetime.datetime.now() + datetime.timedelta(minutes=10)

        # Send OTP via email
        subject = "CourseFinder verification"
        message = f"Here is your OTP for registration: {otp}. It is valid for 10 minutes."
        send_mail(subject, message, settings.EMAIL_HOST_USER, [email])

        return Response({
            "message": "OTP sent successfully.",
            "otp": otp,
            "expiry": expiry_time.strftime('%Y-%m-%d %H:%M:%S')
        }, status=status.HTTP_200_OK)

# To register as studnet
class StudentRegisterView(generics.CreateAPIView):
    serializer_class = StudentSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        
        print("Verified status received:", request.data.get("verified"))

        if not request.data.get("verified", False):
            return Response({"error": "Email verification is required."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            student = serializer.save()
            refresh = RefreshToken.for_user(student.user)

            return Response({
                "id": student.user.id,
                "username": student.user.username,
                "email": student.user.email,
                "role": student.user.role,
                "access_token": str(refresh.access_token),
                "refresh_token": str(refresh),
                "message": "Student registration successful"
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# To register as college
class CollegeRegisterView(generics.CreateAPIView):
    serializer_class = CollegeDetailSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            college = serializer.save()
            refresh = RefreshToken.for_user(college.user)

            return Response({
                "id": college.user.id,
                "name": college.name,
                "email": college.user.email,
                "role": college.user.role,
                "access_token": str(refresh.access_token),
                "refresh_token": str(refresh),
                "message": "College registered successfully"
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# To add courses to a college
class AddCourseView(generics.CreateAPIView):
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        user = request.user

        if not hasattr(user, 'college_profile'):
            return Response({"error": "Only colleges can add courses."}, status=status.HTTP_403_FORBIDDEN)

        college = user.college_profile

        courses_data = request.data
        if not isinstance(courses_data, list):
            return Response({"error": "Expected a list of courses."}, status=status.HTTP_400_BAD_REQUEST)

        created_courses = []
        errors = []

        for course_data in courses_data:
            course_data['college'] = college.id
            serializer = self.get_serializer(data=course_data)

            if serializer.is_valid():
                created_courses.append(serializer.save())
            else:
                errors.append(serializer.errors)

        if errors:
            return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": "Courses added successfully"}, status=status.HTTP_201_CREATED)

# To get all colleges
class CollegeListView(generics.ListAPIView):
    queryset = College.objects.all()
    serializer_class = CollegeListSerializer
    permission_classes = [AllowAny]

# To get a single college details
class CollegeDetailView(generics.RetrieveAPIView):
    queryset = College.objects.all()
    serializer_class = CollegeDetailSerializer
    permission_classes = [AllowAny]

# To get filter data
class FilterDataView(views.APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        unique_courses = []
        seen_courses = set()
        for course in Course.objects.all():
            course_name_lower = course.name.lower()
            if course_name_lower not in seen_courses:
                seen_courses.add(course_name_lower)
                unique_courses.append(course)

        courses_data = UniqueCourseSerializer(unique_courses, many=True).data
        locations_data = AllLocationsSerializer(College.objects.all(), many=True).data

        return Response({
            "courses": courses_data,
            "locations": locations_data
        }, status=status.HTTP_200_OK)

# To apply to a college
class ApplyToCollegeView(generics.CreateAPIView):
    serializer_class = ApplicationSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save()

# To check applied colleges and courses of a student
class AppliedCollegesView(generics.ListAPIView):
    serializer_class = ApplicationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        print("Authenticated User:", user)

        try:
            student = Student.objects.get(user=user)
            return Application.objects.filter(student=student)
        except Student.DoesNotExist:
            return Application.objects.none()

# To add and retrive reviews
class ReviewListCreateView(generics.ListCreateAPIView):
    serializer_class = ReviewSerializer
    
    def get_permissions(self):
        if self.request.method == "GET":
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        college_id = self.kwargs['college_id']
        return Review.objects.filter(college_id=college_id)

    def perform_create(self, serializer):
        user = self.request.user

        if not hasattr(user, 'student_profile'):
            raise serializers.ValidationError({"student": ["Invalid student profile."]})

        student = user.student_profile
        college_id = self.kwargs['college_id']

        college = College.objects.filter(id=college_id).first()
        if not college:
            raise PermissionDenied("Invalid college ID")

        serializer.save(student=student, college=college)

# To update and view student
class UserStudentUpdateView(generics.RetrieveUpdateAPIView):
    serializer_class = UpdateStudentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user.student_profile

# To update and view student
class CollegeUpdateView(generics.RetrieveUpdateDestroyAPIView):
    queryset = College.objects.all()
    serializer_class = CollegeUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, *args, **kwargs):
        college = get_object_or_404(College, id=kwargs["pk"])
        
        if request.user != college.user:
            return Response({"error": "Permission denied"}, status=403)
        
        serializer = CollegeUpdateSerializer(college, data=request.data, partial=False)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

# To get all college applications
class CollegeApplicationsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            college = request.user.college_profile
        except College.DoesNotExist:
            return Response({"error": "You are not associated with any college"}, status=403)

        applications = Application.objects.filter(college=college)
        serializer = AppliedStatusSerializer(applications, many=True)
        return Response(serializer.data)

# To update the status of an application
class UpdateApplicationStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, application_id):

        try:
            college = request.user.college_profile
        except College.DoesNotExist:
            return Response({"error": "You are not associated with any college"}, status=403)

        application = get_object_or_404(Application, id=application_id, college=college)
        
        new_status = request.data.get('status')
        if new_status not in ['approved', 'rejected']:
            return Response({"error": "Invalid status"}, status=400)

        application.status = new_status
        application.save()
        return Response({"message": f"Application status updated to {new_status}"})

# Edit college details
class CollegeDetailUpdateView(generics.RetrieveUpdateAPIView):
    serializer_class = CollegeEditSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return get_object_or_404(College, user=self.request.user)

# Approve college
class ApproveCollegeView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def patch(self, request, college_id):
        college = get_object_or_404(College, id=college_id)
        college.is_approved = True
        college.save()
        return Response({"message": f"College '{college.name}' has been approved."}, status=200)

# Delete college
class DeleteCollegeView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def delete(self, request, college_id):
        college = get_object_or_404(College, id=college_id)
        college_name = college.name
        college.delete()
        return Response({"message": f"College '{college_name}' has been deleted."}, status=200)

# Fetch all courses of a college and update/delete a course
class CourseManagementView(generics.ListCreateAPIView, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Get all courses for the logged-in college user.
        """
        user = self.request.user
        if not hasattr(user, 'college_profile'):
            return Course.objects.none()

        return Course.objects.filter(college=user.college_profile)

    def put(self, request, pk, *args, **kwargs):
        """
        Update a course details.
        """
        course = get_object_or_404(Course, id=pk)
        if request.user.college_profile != course.college:
            return Response({"error": "You don't have permission to update this course."}, status=status.HTTP_403_FORBIDDEN)

        serializer = CourseSerializer(course, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, *args, **kwargs):
        """
        Delete a course.
        """
        course = get_object_or_404(Course, id=pk)
        if request.user.college_profile != course.college:
            return Response({"error": "You don't have permission to delete this course."}, status=status.HTTP_403_FORBIDDEN)

        course.delete()
        return Response({"message": "Course deleted successfully."}, status=status.HTTP_204_NO_CONTENT)

# To get all the students
class UsersExcludingAdminView(generics.ListAPIView):
    serializer_class = StudentSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return Student.objects.exclude(user__role="admin")
    
# To get all the reviews
class AllReviewsView(generics.ListAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.AllowAny]

# Contact view
class ContactMessageView(generics.ListCreateAPIView):
    serializer_class = ContactSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Contact.objects.all()
        return Contact.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)    

# Initialize GROQ client
client = groq.Client(api_key="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")

def get_groq_response(user_input):
    system_prompt = {
        "role": "system",
        "content": "You are a helpful assistant. You reply with very short answers."
    }

    chat_history = [system_prompt]
    chat_history.append({"role": "user", "content": user_input})

    chat_completion = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=chat_history,
        max_tokens=100,
        temperature=1.2
    )

    response = chat_completion.choices[0].message.content
    response = re.sub(r'\*(.*?)\*', r'<b>\1</b>', response)  # Format bold text

    return response

@method_decorator(csrf_exempt, name='dispatch')
class ChatbotView(View):
    
    def post(self, request):        
        try:
            body = json.loads(request.body)
            user_input = body.get('userInput')
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format."}, status=400)

        if not user_input:
            return JsonResponse({"error": "No user input provided."}, status=400)  

        static_responses = {
            "hi": "Hello! How can I assist you today?",
            "hello": "Hi there! How can I help you?",
            "how are you": "I'm just a chatbot, but I'm doing great! How about you?",
            "bye": "Goodbye! Take care.",
            "whats up": "Not much, just here to help you with queries. How can I help you today?",
        }

        lower_input = user_input.lower().strip()
        if lower_input in static_responses:
            return JsonResponse({'response': static_responses[lower_input]}, status=200)

        try:
            data = get_groq_response(user_input)
            return JsonResponse({'response': data}, status=200)
        except Exception as e:
            return JsonResponse({"error": f"Failed to get GROQ response: {str(e)}"}, status=500)

def get_csrf_token(request):
    return JsonResponse({'csrfToken': get_token(request)})

