from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import *
from django.contrib.auth import get_user_model

# admin register serializer
class AdminRegSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'role']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)

# user login serializer
class LoginSerializer(serializers.Serializer):
    
    email = serializers.CharField()
    password = serializers.CharField(write_only=True)

# student serializer
class StudentSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', max_length=150)
    email = serializers.EmailField(source='user.email')
    password = serializers.CharField(write_only=True, source='user.password', min_length=6)
    verified = serializers.BooleanField()

    class Meta:
        model = Student
        fields = ['username', 'email', 'password', 'phone_number', 'date_of_birth',
                  'gender', 'school_name', 'highest_qualification', 'marks_percentage',
                  'passing_year', 'street', 'district', 'state', 'verified']

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        verified = validated_data.pop('verified', False)

        if not verified:
            raise serializers.ValidationError({"verified": "Email is not verified."})

        user = User.objects.create(
            username=user_data['username'],
            email=user_data['email'],
            role='student',
            password=make_password(user_data['password'])
        )

        student = Student.objects.create(user=user, verified=verified, **validated_data)

        return student

# Course serializer
class CourseSerializer(serializers.ModelSerializer):
    college = serializers.PrimaryKeyRelatedField(queryset=College.objects.all())

    class Meta:
        model = Course
        fields = ['id', 'college', 'name', 'duration', 'fee']

    def create(self, validated_data):
        return Course.objects.create(**validated_data)

# Unique course serializer
class UniqueCourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['name']

# All locations
class AllLocationsSerializer(serializers.ModelSerializer):
    class Meta:
        model = College
        fields = ['state', 'district']

# College serializer
class CollegeDetailSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', max_length=150)
    email = serializers.EmailField(source='user.email')
    password = serializers.CharField(write_only=True, source='user.password', min_length=6)
    courses = CourseSerializer(many=True, read_only=True)

    class Meta:
        model = College
        fields = ['username', 'email', 'password', 'name', 'street', 'state', 'district', 
                  'description', 'logo', 'image', 'courses']

    def create(self, validated_data):
        user_data = validated_data.pop('user')

        user = User.objects.create(
            username=user_data['username'],
            email=user_data['email'],
            role='college',
            password=make_password(user_data['password'])
        )
        college = College.objects.create(user=user, **validated_data)
        return college

# List all colleges
class CollegeListSerializer(serializers.ModelSerializer):
    courses = CourseSerializer(many=True, read_only=True, required=False)

    class Meta:
        model = College
        fields = ['id', 'name', 'logo', 'image', 'state', 'district', 'street', 'is_approved', 'courses']

# To apply for a college
class ApplicationSerializer(serializers.ModelSerializer):
    student = serializers.PrimaryKeyRelatedField(queryset=Student.objects.all(), required=False)
    college_name = serializers.CharField(source='college.name', read_only=True)
    course_name = serializers.CharField(source='course.name', read_only=True)

    class Meta:
        model = Application
        fields = ['id', 'student', 'college', 'college_name', 'course', 'course_name', 'status', 'payment_id', 'applied_at']
        read_only_fields = ['applied_at']

    def create(self, validated_data):
        request = self.context.get('request')
        student = Student.objects.get(user=request.user)

        if Application.objects.filter(student=student, college=validated_data['college'], course=validated_data['course']).exists():
            raise serializers.ValidationError("You have already applied for this course.")

        if not validated_data.get('payment_id'):
            raise serializers.ValidationError("Payment ID is required to apply.")

        validated_data['student'] = student
        return super().create(validated_data)

# To add review
class ReviewSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.user.username", read_only=True)
    college_name = serializers.CharField(source="college.name", read_only=True)
    student = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'student', 'student_name', 'college', 'college_name', 'rating', 'review_text', 'created_at']
        read_only_fields = ['id', 'student', 'student_name', 'college_name', 'created_at']

# Fetch and update student details
class UpdateStudentSerializer(serializers.ModelSerializer):
    User = get_user_model()

    username = serializers.CharField(source='user.username', max_length=150, required=False)
    email = serializers.EmailField(source='user.email', required=False)
    password = serializers.CharField(write_only=True, source='user.password', min_length=6, required=False)
    gender = serializers.CharField(required=False)
    
    class Meta:
        model = Student
        fields = ['username', 'email', 'password', 'phone_number', 'date_of_birth',
                  'gender', 'school_name', 'highest_qualification', 'marks_percentage',
                  'passing_year', 'street', 'district', 'state']

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})

        user = instance.user
        if 'username' in user_data:
            user.username = user_data['username']
        if 'email' in user_data:
            user.email = user_data['email']
        if 'password' in user_data:
            user.password = make_password(user_data['password'])
        user.save()

        for attr, value in validated_data.items():
            if value is not None:
                setattr(instance, attr, value)

        instance.save()

        return instance

# Fetch and update college details
class CollegeUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = College
        fields = '__all__'
        read_only_fields = ['is_approved']

# To fetch and update student applications
class AppliedStatusSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.user.username', read_only=True)
    email = serializers.EmailField(source='student.user.email', read_only=True)
    phone_number = serializers.CharField(source='student.phone_number', read_only=True)
    gender = serializers.CharField(source='student.gender', read_only=True)
    school_name = serializers.CharField(source='student.school_name', read_only=True)
    highest_qualification = serializers.CharField(source='student.highest_qualification', read_only=True)
    marks_percentage = serializers.DecimalField(source='student.marks_percentage', max_digits=5, decimal_places=2, read_only=True)
    passing_year = serializers.IntegerField(source='student.passing_year', read_only=True)
    street = serializers.CharField(source='student.street', read_only=True)
    district = serializers.CharField(source='student.district', read_only=True)
    state = serializers.CharField(source='student.state', read_only=True)
    course_name = serializers.CharField(source='course.name', read_only=True)

    class Meta:
        model = Application
        fields = [
            'id', 'student_name', 'email', 'phone_number', 'gender', 
            'school_name', 'highest_qualification', 'marks_percentage', 'passing_year',
            'street', 'district', 'state', 'course_name', 'status'
        ]

# College update
class CollegeEditSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    password = serializers.CharField(write_only=True, source='user.password', min_length=6, required=False)
    courses = CourseSerializer(many=True, read_only=True)

    class Meta:
        model = College
        fields = ['username', 'email', 'password', 'name', 'street', 'state', 'district', 
                  'description', 'logo', 'image', 'courses']

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})

        user = instance.user
        if 'username' in user_data:
            user.username = user_data['username']
        if 'email' in user_data:
            user.email = user_data['email']
        if 'password' in user_data:
            user.password = make_password(user_data['password'])
        user.save()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance

# College approval
class CollegeApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = College
        fields = ['id', 'name', 'is_approved']

# To add and get contact messages
class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = '__all__'

