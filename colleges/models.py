from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator

# User Model
class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('student', 'Student'),
        ('college', 'College'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')

    groups = models.ManyToManyField(
        "auth.Group",
        related_name="custom_user_groups",
        blank=True
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        related_name="custom_user_permissions",
        blank=True
    )

    def __str__(self):
        return self.username

# Student Model
class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="student_profile")
    
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, null=True, blank=True)
    
    school_name = models.CharField(max_length=255, blank=True, null=True)
    highest_qualification = models.CharField(max_length=255, blank=True, null=True)
    marks_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)]
    )
    passing_year = models.PositiveIntegerField(blank=True, null=True)
    
    street = models.CharField(max_length=100, blank=True, null=True)
    district = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)

    verified = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

# College Model
class College(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="college_profile")

    name = models.CharField(max_length=255, blank=True, null=True)
    logo = models.ImageField(upload_to='college_logos/', blank=True, null=True)
    image = models.ImageField(upload_to='college_images/', blank=True, null=True)

    street = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    district = models.CharField(max_length=100, blank=True, null=True)

    description = models.TextField(blank=True, null=True)
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return self.name

# Course Model
class Course(models.Model):
    college = models.ForeignKey(College, on_delete=models.CASCADE, related_name="courses")

    name = models.CharField(max_length=255)
    duration = models.PositiveIntegerField()
    fee = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.name} - {self.college.name}"

# College applly
class Application(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="applications")
    college = models.ForeignKey(College, on_delete=models.CASCADE, related_name="applications")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="applications")
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    payment_id = models.CharField(max_length=255, unique=True)
    applied_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.user.username} - {self.course.name} ({self.college.name})"

# Review Model
class Review(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="reviews")
    college = models.ForeignKey(College, on_delete=models.CASCADE, related_name="reviews")

    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    review_text = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.user.username} - {self.college.name} ({self.rating} Stars)"
    
# Contact Model
class Contact(models.Model):
    
    User = get_user_model()

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="contact_messages")
    name = models.CharField(max_length=255)
    email = models.EmailField()
    subject = models.CharField(max_length=255)
    message = models.TextField()
    role = models.CharField(max_length=10, choices=[('student', 'Student'), ('college', 'College')], default='student')
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.role}) - {self.subject}"

