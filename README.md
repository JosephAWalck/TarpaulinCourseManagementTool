# TarpaulinCourseManagementTool

## Summary of Endpoints

|     | Functionality                 | Endpoint                    | Protection                                         | Description |
| --- | ----------------------------- | --------------------------- | -------------------------------------------------- | ----------- |
| 1.  | User login                    | POST /users/login           | Pre-created Auth0 users with username and password | User Auth0 to issue JWTs. |
| 2.  | Get all users                 | GET /users                  | Admin Only                                         | Summary information of all 9 users. No info about avatar or courses. |
| 3.  | Get a user                    | GET /users/:id              | Admin or user with HWT matching id                 | Detailed info about the user, including avatar (if any) and courses (for instructors and students). | 
| 4.  | Create/update a user's avatar | POST /users/:id/avatar      | User with JWT matching id                          | Upload file to Google Cloud Storage. |
| 5.  | Get a user's avatar           | GET /users/:id/avatar       | User with JWT matching id                          | Read and return file from Google Cloud Storage. | 
| 6.  | Delete a user's avatar        | DELETE /users/:id/avatar    | User with JWT matching id                          | Delete file from Google Cloud Storage. |
| 7.  | Create a course               | POST /courses               | Admin only                                         | Create a course. |
| 8.  | Get all courses               | GET /courses                | Unprotected                                        | Paginated information of all courses. Page size is 3 and ordered by "subject." Doesn't return info on course enrollment. | 
| 9.  | Get a course                  | GET /course/:id             | Unprotected                                        | Information about a course. Doesn't return info on course enrollment. |
| 10. | Update a course               | PATCH /course/:id           | Admin only                                         | Partial update. |
| 11. | Delete a course               | DELETE /course/:id          | Admin only                                         | Delete course and enrollment info about the course. |
| 12. | Update enrollment in a course | PATCH /course/:id/students  | Admin or instructor of the course                  | Enroll or disenroll students from the course. |
| 13. | Get enrollment for a course   | GET /courses/:id/students   | Admin or instructor of the course                  | All students enrolled in the course. |

## 1. User Login 

### Request

    POST /users/login

### Request Body

    {
     "username": string,
     "password": string
    }

### Response Body

Status: 200
    
    {
      "token": string
    }

Status: 400

    {"Error": "The request body is invalid"}

Status: 401

    {"Error": "Unauthorized"}

## 2. Get All Users

### Request 

    GET /users

    Header: JWT as bearer token in the Authorization header

### Protection

Only users with the admin role

### Response body

Status: 200

    [
      {
        "id": int,
        "role": "student" | "instructor" | "admin",
        "sub": string
      },
      {
        "id": int,
        "role": "student" | "instructor" | "admin",
        "sub": string
      },
      ...
    ]

## 3. Get a User

### Request

    GET /users

    Header: JWT as bearer token in the Authorization header

### Protection

Only users with the admin role

### Path Parameters 

user_id: ID of the user

### Response Body

Status: 200

    {
      "avatar_url": "http://placeholder_url/users/{user_id: int}/avatar",
      "courses": [
        "http://placeholder_url/courses/{course_id: int}",
        "http://placeholder_url/courses/{course_id: int}"
      ],
      "id": int,
      "role": "student" | "instructor" | "admin",
      "sub": string
    }

Status: 401

    {"Error": "Unauthorized"}

Status: 403

    {"Error": "You don't have permission on this resource"}

## 4. Create/Update a User's Avatar

### Request

    POST /users/:user_id/avatar

    Header: JWT as bearer token in the Authorization header

### Protection

JWT is owned by user_id in the path parameter.

### Path Parameters

user_id: ID of the user

### Request Body

Form-data with one required key "file"

### Response

Status: 200

    No response body

Status: 400

    {"Error": "The request body is invalid"}

Status: 401

    {"Error": "Unauthorized"}

Status: 403

    {"Error": "You don't have permission on this resource"}

## 5. Get a User's Avatar

### Request 

    GET /users/:user_id/avatar

    Header: JWT as bearer token in the Authorization header

### Protection

JWT is owned by user_id in the path parameter

### Path Parameters

user_id: ID of the user

### Response

Status: 200

    No response Body

Status: 401

    {"Error": "Unauthorized"}

Status: 403

    {"Error": "You don't have permission on this resource"}

Status: 404

    {"Error": "Not found"}    
    
## 6. Delete a User's Avatar

### Request

    DELETE /users/:user_id/avatar

    Header: JWT as bearer token in the Authorization header

### Protection

JWT s owned by user_id in the path parameter

### Path Parameters

user_id: ID of the user

### Response

Status: 204

    No response body

Status: 401

    {"Error": "Unauthorized"}

Status: 403

    {"Error": "You don't have permission on this resource"}

Status: 404

    {"Error": "Not found"}    

## 7. Create a Course

### Request

    POST /courses

    Header: JWT as bearer token in the Authorization header

### Protection

Only users with the admin role

### Request Body

    {
      "subject": string,
      "number": string,
      "title": string,
      "term": string,
      "instructor_id": {user_id: int}
    }

### Response

Status: 201

    {
      "id": {course_id: int},
      "instructor_id": {instructor_id: int},
      "number": string,
      "self": "http://placeholder_url/courses/{course_id: int}",
      "subject": string,
      "term": string,
      "title": string
    }

Status: 400

    {"Error": "The request body is invalid"}

Status: 401

    {"Error": "Unauthorized"}

Status: 403

    {"Error": "You don't have permission on this resource"}
    
## 8. Get All Courses

### Request

    GET /courses
    GET /courses?offset=3&limit=3
    ...

### Query Parameters

offset: Offset value 
limit: Limit value = 3

### Response

Status: 200

    {
    "courses": [
      {
        "id": {course_id: int},
        "instructor_id": {user_id: int},
        "number": int,
        "self": "http://placeholder_url/courses/{course_id: int}",
        "subject": string,
        "term": string,
        "title": string
      },
      {
        "id": {course_id: int},
        "instructor_id": {user_id: int},
        "number": int,
        "self": "http://placeholder_url/courses/{course_id: int}",
        "subject": string,
        "term": string,
        "title": string
      },
      {
        "id": {course_id: int},
        "instructor_id": {user_id: int},
        "number": int,
        "self": "http://palceholder_url/courses/{course_id: int}",
        "subject": string,
        "term": string,
        "title": string
      }
    ],
    "next": "http://placeholder_url/courses?limit=3&offset=3"
    }    

## 9. Get a Course

### Request

    GET /courses/:course_id

### Path Parameters

cousre_id: ID of the course

### Response 

Status: 200

    {
      "id": {course_id: int},
      "instructor_id": {instructor_id: int},
      "number": int,
      "self": "http://placeholder_url/courses/{course_id: int}",
      "subject": string,
      "term": string,
      "title": string
    }

Status: 404 

    {"Error": "Not found"}

## 10. Update a Course

### Request

    PATCH /courses/:course_id

    Header: JWT as bearer token in the Authorization header

### Protection

Only users with the admin role

### Path Parameters

course_id: ID of the course

### Request Body

Any property which is not specified in the request will remain unchanged

    {
      "instructor_id": {user_id: int},
      "number": string,
      "self": "http://placeholder_url/courses/{course_id: int}",
      "subject": string,
      "term": string,
      "title": string
    }    

Status: 400

    {"Error": "The request body is invalid"}

Status: 401

    {"Error": "Unauthorized"}

Status: 403

    {"Error": "You don't have permission on this resource"}

## 11. Delete a Course

### Request

    DELETE /courses/:course_id
    
    Header: JWT as bearer token in the Authorization header

### Protection

Only users with the admin role

### Path Parameters

course_id: ID of the course

### Response

Status: 204

    No response body

Status: 401

    {"Error": "Unauthorized"}

Status: 403

    {"Error": "You don't have permission on this resource"}

## 12. Update Enrollment in a Course

### Request 

    PATCH /courses/:course_id/students

    Header: JWT as bearer token in the Authorization header

### Protection

User with admin role or JWT is owned by the instructor of this course

### Path Parameters

course_id: ID of the course

### Request Body

    {
     "add": [
       {user_id: int},
       {user_id: int},
       {user_id: int},
       {user_id: int},
     ],
     "remove": [
       {user_id: int},
       {user_id: int},
       {user_id: int},
     ]
    }

### Response Body

Status: 200

    No response body

Status: 401

    {"Error": "Unauthorized"}

Status: 403

    {"Error": "You don't have permission on this resource"}

Status: 409

    {"Error": "Enrollment data is invalid"}
    
## 13. Get Enrollment for a Course

### Request 

    GET /courses/:course_id/students

    Header: JWT as bearer token in the Authorization header

### Protection

User with admin rol or when JWT is owned by the instructor of this course

### Path Parameters

course_id: ID of the course

### Response Body

Status: 200

    [
      {user_id: int},
      {user_id: int},
      {user_id: int},
    ]    

Status: 401

    {"Error": "Unauthorized"}

Status: 403

    {"Error": "You don't have permission on this resource"}    
