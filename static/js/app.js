angular.module('klssignin', ['ngRoute'])
.config(function($routeProvider) {
  $routeProvider
  .when('/', {
    templateUrl:'templates/signin.html',
    controller: 'SigninCtrl'
  })
  .when('/admin/user-dashboard', {
      templateUrl:'templates/admin_user_dashboard.html',
      controller: 'AdminUserDashCtrl'
  })
  .when('/whosinclass', {
      templateUrl:'templates/whosinclass.html',
      controller: 'WhosInClassCtrl'
  })
  .otherwise({
    redirectTo: '/'
  })
  ;
})
.controller('MainCtrl', function($scope) {

})
.controller('SigninCtrl', function($scope, $http, $location) {
  $scope.errorMessage = undefined;
  $scope.success = false;

  $scope.login = function(user) {
    $http.get('/signinout', {
      "params": {"username" : user.name}
    })
    .success(function(data,status) {
      if (data['is-child']) {
        $scope.student = {
          username: data['username'],
          inClass: data['in-class']
        };
      } else {
        $scope.children = data['children']
      }
      $scope.success = true;
    }).error(function(data,status) {
      // 500 errors aren't our problem.
      if (status == 500) return;
      // if it's a 400 error, display the message to the client.
      if (status == 400) {
        $scope.errorMessage = data.message;
      }
    })
  }
})

.controller('WhosInClassCtrl', function($scope, $http) {
  $scope.students = {
    present: [],
    absent: [],
    nothere: []
  };
  $http.get('/whosinclass')
  .success(function(data,status) {
    $scope.students.present = data.present || [];
    $scope.students.absent = data.absent || [];
    $scope.students.nothere = data.nothere || [];
  })
})
.controller('AdminUserDashCtrl', function($scope, $http, $location) {
    $scope.users = [];
    $http.get("/users").success(function(data) {
        $scope.users = data;
    });
    $scope.students = [];
    $http.get("/students").success(function(data) {
        $scope.students = data;
        console.log($scope.students);
    });

    $scope.delete_user = function(user) {
        console.log("Deleting " + user);
        $scope.users[user].deleted = true;
        $http.put("/users", {"username":  user, "params": $scope.users[user]}).success(function() {
            $http.get("/users").success(function(data) {
                $scope.users = data;
            });
        });
    };

    $scope.update_user = function(username) {
        console.log("Updating " + username);
        $http.put("/users", {"username": username, "params": $scope.users[username]});
    };

    $scope.create_user = function() {
        var user = "John";
        console.log("Creating " + user);
        $http.post("/users", {"username": user});
    };

    $scope.delete_student = function(student) {
        console.log("Deleting " + student);
        $scope.students[student].deleted = true;
        $http.put("/students", {"username": student, "params": $scope.students[student]}).success(function() {
            $http.get("/students").success(function(data) {
                $scope.students = data;
            });
        });
    };

    $scope.update_student = function(student) {
        console.log("Updating " + student);
        $http.put("/students", {"username": student, "params": $scope.students[student]});
    };

    $scope.patch_student = function(student, param) {
        console.log("Updating " + student + " parameter: " + param);
        $http.put("/students/patch", {"username": student, "param": [param, $scope.students[student][param]]});
    };

    $scope.create_student = function() {
        var student = "Sally";
        console.log("Creating " + student);
        $http.post("/students", {"username": student});
    };
})
;
