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
        $http.delete("/users", {params: {username: user}});
    };

    $scope.update_user = function(user) {
        console.log("Updating " + user);
        // TODO (phillip) Should only update the given params
        $http.put("/users", {"username": user, "params": {"students": ["Hank"]}});
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
            window.location.reload(false);
        });
    };

    $scope.update_student = function(student) {
        console.log("Updating " + student);
        // TODO (phillip) Should only update the given params
        $http.put("/students", {"username": student, "params": $scope.students[student]});
    };

    $scope.create_student = function() {
        var student = "Sally";
        console.log("Creating " + student);
        $http.post("/students", {"username": student});
    };
})
;
