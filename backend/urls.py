"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from colleges.views import *
from django.urls import path
from django.conf import settings
from django.contrib import admin
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('csrf/', get_csrf_token, name='get_csrf_token'),
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path('login/', Login.as_view(), name='login'),
    path('sendotp/', RequestOTPView.as_view(), name='request-otp'),
    path('adminregister/', AdminRegisterView.as_view(), name='admin-register'),
    path('studentregister/', StudentRegisterView.as_view(), name='student-register'),
    path('collegeregister/', CollegeRegisterView.as_view(), name='college-register'),
    path('colleges/', CollegeListView.as_view(), name='college-list'),
    path('college/<int:pk>/', CollegeDetailView.as_view(), name='college-detail'),
    path('addcourse/', AddCourseView.as_view(), name='add-course'),
    path('filterdata/', FilterDataView.as_view(), name='all-courses'),
    path('apply/', ApplyToCollegeView.as_view(), name='apply-to-college'),
    path('applied-colleges/', AppliedCollegesView.as_view(), name='applied-colleges'),
    path('colleges/<int:college_id>/reviews/', ReviewListCreateView.as_view(), name='college-reviews'),
    path('student/update/', UserStudentUpdateView.as_view(), name='user-student-update'),
    path('college/update/<int:pk>/', CollegeUpdateView.as_view(), name='college-update'),
    path('college/applications/', CollegeApplicationsView.as_view(), name='college-applications'),
    path('college/application/<int:application_id>/update/', UpdateApplicationStatusView.as_view(), name='update-application-status'),
    path('college/profile/', CollegeDetailUpdateView.as_view(), name='college-profile'),
    path('college/approve/<int:college_id>/', ApproveCollegeView.as_view(), name='approve-college'),
    path('college/delete/<int:college_id>/', DeleteCollegeView.as_view(), name='delete-college'),
    path('courses/', CourseManagementView.as_view(), name='college-courses'),
    path('courses/<int:pk>/', CourseManagementView.as_view(), name='course-update-delete'),
    path('chatbot/', ChatbotView.as_view(), name='chatbot'),
    path('all-users/', UsersExcludingAdminView.as_view(), name="all-users"),
    path('all-reviews/', AllReviewsView.as_view(), name="all-reviews"),
    path('contact/message/', ContactMessageView.as_view(), name="contact-messages"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)