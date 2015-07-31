angular.module('klssignin', ['ngRoute', 'ngSanitize'])
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
  .when('/admin/interactions', {
    templateUrl:'templates/interactions.html',
    controller: 'InteractionCtrl'
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
  });

  //TODO(vishesh): make this poll the server every 5 minutes for data
  // so that it remains up to date.
})

.controller('InteractionCtrl', function($scope, $http) {
  $scope.interactions = []
  $http.get('/interactions')
  .success(function(data) {
    $scope.interactions = data.interactions;
    console.log($scope.interactions)
  });
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
    $http.delete("/students", {params: {"username": student}})
    .success(function() {
      window.location.reload(false);
    });
  };

  $scope.update_student = function(student) {
    console.log("Updating " + student);
    // TODO (phillip) Should only update the given params
    $http.put("/students", {"username": student,
                            "params": $scope.students[student]});
  };

  $scope.create_student = function() {
    var student = "Sally";
    console.log("Creating " + student);
    $http.post("/students", {"username": student});
  };
})

.directive('contenteditable', function() {
  return {
    restrict: 'A',
    require: 'ngModel',
    scope: false,
    transclude: false,
    link: function(scope, elm, attrs, ctrl) {
      elm.bind('keydown', function(event) {
        // esc should revert the value
        if (event.which == 27) {
          event.preventDefault();
          elm.html(ctrl.$viewValue);
          // TODO(vishesh): this isn't a full solution because
          // contenteditable could be many elements deep.
          // This only works if contenteditable is used on a leaf DOM node.
          event.target.blur();
        }
        // enter should store the value
        if (event.which == 13) {
          event.preventDefault();
          event.target.blur();
        }
      });

      // view -> model
      elm.bind('blur', function() {
        scope.$apply(function() {
          ctrl.$setViewValue(elm.text().trim());
        });
      });

      // model -> view
      ctrl.$render = function() {
        elm.html(ctrl.$viewValue);
      };
    }
  };
})

.filter('startat', function() {
    return function(input, start) {
        if(input) {
            start = +start; //parse to int
            return input.slice(start);
        }
        return [];
    }
})

.filter('time', function() {
  return function(input, infmt, fmt) {
    if (input) {
      var m = moment(input, infmt || 'YYYY-MM-DD').format(fmt || 'MMMM Do YYYY');
      return m === 'Invalid Date' ? input : m;
    }
    return input;
  }
})

.filter('transform', function() {
  return function(input, from, to) {
    if (input === from) return to || '';
    return input;
  }
})

;
