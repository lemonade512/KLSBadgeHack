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
    $scope.adults = [];
    $http.get("/adults").success(function(data) {
        $scope.adults = _.pairs(data);
    });

    $scope.delete_adult = function(adult) {
        console.log("Deleting " + adult);
        $http.delete("/adults", {params: {username: adult}});
    };

    $scope.update_adult = function(adult) {
        console.log("Updating " + adult);
        // TODO (phillip) Should only update the given params
        $http.put("/adults", {"username": adult, "params": {"students": ["Hank"]}});
    };

    $scope.create_adult = function() {
        var adult = "John";
        console.log("Creating " + adult);
        $http.post("/adults", {"username": adult});
    };

    $scope.delete_student = function(student) {
        console.log("Deleting " + student);
        $http.delete("/students", {params: {"username": student}});
    };

    $scope.update_student = function(student) {
        console.log("Updating " + student);
        // TODO (phillip) Should only update the given params
        $http.put("/students", {"username": student, "params": {"can_signout": true}});
    };

    $scope.create_student = function(student) {
        console.log("Creating " + student);
        $http.post("/students", {"username": student});
    };
})
;
