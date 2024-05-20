# SPDX-FileCopyrightText: 2024 Amgen
#
# SPDX-License-Identifier: BSD-3-Clause

"Test the gaussian regressor"

import shutil
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn.gaussian_process
from sklearn.gaussian_process.kernels import Kernel, WhiteKernel

from gumps.solvers.regressors.gaussian_regressor import GaussianRegressor, GaussianRegressionParameter
from gumps.solvers.regressors.regression_solver import RegressionParameters
from gumps.solvers.regressors.regression_loader import load_regressor
from gumps.scalers.standard_scaler import StandardScaler
from gumps.scalers.log_combo_scaler import LogComboScaler
from gumps.solvers.regressors.regressor_data import DataRegression


def generate_regression_parameters(count: int = 5):
    "generate regression parameters"
    input_data = pd.DataFrame({"x": np.linspace(0, 1, count)})
    output_data = pd.DataFrame({"y": np.linspace(0, 1, count)})
    return GaussianRegressionParameter(input_data=input_data, output_data=output_data)

class TestGaussianRegressionSolver(unittest.TestCase):
    "test the gaussian process regressor"

    def test_initialize_kernel_none(self):
        "test the initialization of the kernel when it is None"
        parameters = generate_regression_parameters()
        regressor = GaussianRegressor(parameters, kernel=None)
        self.assertIsInstance(regressor.parameters, GaussianRegressionParameter)
        self.assertIsInstance(regressor.kernel, Kernel)
        self.assertIsInstance(regressor.data_regression.input_scaler, LogComboScaler)
        self.assertIsInstance(regressor.data_regression.output_scaler, LogComboScaler)
        self.assertIsInstance(regressor.data_regression.input_scaler.scaler, StandardScaler)
        self.assertIsInstance(regressor.data_regression.output_scaler.scaler, StandardScaler)
        self.assertIsInstance(regressor.regressor,
                              sklearn.gaussian_process.GaussianProcessRegressor)
        self.assertIsInstance(regressor.data_regression, DataRegression)

    def test_initialize_kernel_not_none(self):
        "test the initialization of the kernel when it is not None"
        kernel = WhiteKernel()
        parameters = generate_regression_parameters()
        regressor = GaussianRegressor(parameters, kernel=kernel)
        self.assertIsInstance(regressor.parameters, GaussianRegressionParameter)
        self.assertIsInstance(regressor.kernel, WhiteKernel)
        self.assertIsInstance(regressor.data_regression.input_scaler, LogComboScaler)
        self.assertIsInstance(regressor.data_regression.output_scaler, LogComboScaler)
        self.assertIsInstance(regressor.data_regression.input_scaler.scaler, StandardScaler)
        self.assertIsInstance(regressor.data_regression.output_scaler.scaler, StandardScaler)
        self.assertIsInstance(regressor.regressor,
                              sklearn.gaussian_process.GaussianProcessRegressor)
        self.assertIsInstance(regressor.data_regression, DataRegression)


    def test_initialize_regression_parameters(self):
        "that that initialize works with regression parameters object"
        parameters = generate_regression_parameters()
        parameters  = RegressionParameters(input_data=parameters.input_data,
                                             output_data=parameters.output_data)
        regressor = GaussianRegressor(parameters, kernel=None)
        self.assertIsInstance(regressor.parameters, GaussianRegressionParameter)


    def test_get_regressor(self):
        "test the initialization of the regressor"
        parameters = generate_regression_parameters()
        regressor = GaussianRegressor(parameters)
        reg = regressor._get_regressor()
        self.assertIsInstance(reg, sklearn.gaussian_process.GaussianProcessRegressor)

    def test_regression_parameters(self):
        "test the regression parameters"
        parameters = generate_regression_parameters()
        parameters.alpha = 1e-5
        parameters.n_restarts_optimizer = 10
        parameters.random_state = 10

        regressor = GaussianRegressor(parameters)
        self.assertEqual(regressor.regressor.alpha, 1e-5)
        self.assertEqual(regressor.regressor.n_restarts_optimizer, 10)
        self.assertEqual(regressor.regressor.random_state, 10)

    def test_get_scalers(self):
        "test the initialization of the input and output scalers"
        parameters = generate_regression_parameters()
        regressor = GaussianRegressor(parameters)
        input_scaler, output_scaler = regressor._get_scalers()
        self.assertIsInstance(input_scaler, LogComboScaler)
        self.assertIsInstance(output_scaler, LogComboScaler)

    def test_get_kernel(self):
        "test the initialization of the kernel"
        parameters = generate_regression_parameters()
        regressor = GaussianRegressor(parameters)
        kernel = regressor._get_kernel(WhiteKernel())
        self.assertIsInstance(kernel, WhiteKernel)

    def test_get_kernel_none(self):
        "test the initialization of the kernel when it is None"
        parameters = generate_regression_parameters()
        regressor = GaussianRegressor(parameters)
        kernel = regressor._get_kernel(None)
        self.assertIsInstance(kernel, Kernel)

    def test_save(self):
        "test the save method"
        parameters = generate_regression_parameters()
        regressor = GaussianRegressor(parameters)
        regressor.fit()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir = Path(temp_dir)
            regressor.save(temp_dir)

            self.assertTrue((temp_dir / "regressor.joblib").exists())
            self.assertTrue((temp_dir / "parameters.joblib").exists())
            self.assertTrue((temp_dir / "data").exists())

    def test_load(self):
        "test the load method"
        parameters = generate_regression_parameters()
        regressor = GaussianRegressor(parameters)
        regressor.fit()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir = Path(temp_dir)
            regressor.save(temp_dir)
            new_regressor = GaussianRegressor.load(temp_dir)

            self.assertEqual(str(regressor.regressor), str(new_regressor.regressor))

            self.assertEqual(regressor.data_regression.input_scaler.scaler.scaler.scale_,
                             new_regressor.data_regression.input_scaler.scaler.scaler.scale_)

            self.assertEqual(regressor.data_regression.input_scaler.scaler.scaler.var_,
                             new_regressor.data_regression.input_scaler.scaler.scaler.var_)

            self.assertEqual(regressor.data_regression.output_scaler.scaler.scaler.scale_,
                             new_regressor.data_regression.output_scaler.scaler.scaler.scale_)

            self.assertEqual(regressor.data_regression.output_scaler.scaler.scaler.var_,
                             new_regressor.data_regression.output_scaler.scaler.scaler.var_)

            pd.testing.assert_frame_equal(regressor.predict(parameters.input_data),
                                          new_regressor.predict(parameters.input_data))

    def test_generic_load(self):
        "test the load method"
        parameters = generate_regression_parameters()
        regressor = GaussianRegressor(parameters)
        regressor.fit()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir = Path(temp_dir)
            regressor.save(temp_dir)
            new_regressor = load_regressor(temp_dir)

            self.assertEqual(str(regressor.regressor), str(new_regressor.regressor))

            self.assertEqual(regressor.data_regression.input_scaler.scaler.scaler.scale_,
                             new_regressor.data_regression.input_scaler.scaler.scaler.scale_)

            self.assertEqual(regressor.data_regression.input_scaler.scaler.scaler.var_,
                             new_regressor.data_regression.input_scaler.scaler.scaler.var_)

            self.assertEqual(regressor.data_regression.output_scaler.scaler.scaler.scale_,
                             new_regressor.data_regression.output_scaler.scaler.scaler.scale_)

            self.assertEqual(regressor.data_regression.output_scaler.scaler.scaler.var_,
                             new_regressor.data_regression.output_scaler.scaler.scaler.var_)

            pd.testing.assert_frame_equal(regressor.predict(parameters.input_data),
                                          new_regressor.predict(parameters.input_data))

    def test_fit(self):
        "test the fit method"
        parameters = generate_regression_parameters(count=100)
        regressor = GaussianRegressor(parameters)
        regressor.fit()

    def test_error_metrics(self):
        "test the error metrics method"
        parameters = generate_regression_parameters(count=100)
        regressor = GaussianRegressor(parameters)
        regressor.fit()
        pd.testing.assert_series_equal(pd.Series({'score': 1.0, 'r2_score': 1.0,
                                                  'mean_squared_error': 0.0, 'mse': 0.0,
                                                  'root_mean_squared_error': 0.0, 'rmse': 0.0,
                                                  'normalized_mean_squared_error': 0.0,'nmse': 0.0,
                                                  'normalized_root_mean_squared_error': 0.0, 'nrmse': 0.0}),
                                       regressor.error_metrics(), atol=1e-3, rtol=1e-3)

    def test_predict(self):
        "test the predict method"
        parameters = generate_regression_parameters(count=100)
        regressor = GaussianRegressor(parameters)
        regressor.fit()

        input_data = pd.DataFrame({'x': np.linspace(0, 1, 5)})
        output_data_correct = pd.DataFrame({'y': np.linspace(0, 1, 5)})

        output_data = regressor.predict(input_data)
        pd.testing.assert_frame_equal(output_data_correct, output_data, atol=1e-3, rtol=1e-3)

    def test_predict_with_uncertainty(self):
        "test the predict method with uncertainty"
        parameters = generate_regression_parameters(count=100)
        regressor = GaussianRegressor(parameters)
        regressor.fit()

        input_data = pd.DataFrame({'x': np.linspace(0, 1, 5)})
        output_data_correct = pd.DataFrame({'y': np.linspace(0, 1, 5)})

        output_data, output_std = regressor.predict_uncertainty(input_data)
        pd.testing.assert_frame_equal(output_data_correct, output_data, atol=1e-3, rtol=1e-3)
        self.assertTrue((output_std < 0.001).all()['y'])

    def test_predict_with_uncertainty_exception(self):
        "test the predict method with uncertainty"
        parameters = generate_regression_parameters(count=100)
        regressor = GaussianRegressor(parameters)

        input_data = pd.DataFrame({'x': np.linspace(0, 1, 5)})

        with self.assertRaises(RuntimeError):
            regressor.predict_uncertainty(input_data)


    def test_update_data(self):
        "test the update data method"
        parameters = generate_regression_parameters(count=10)
        regressor = GaussianRegressor(parameters)
        regressor.fit()

        count = 5
        input_data = pd.DataFrame({"x": np.random.rand(count)})
        output_data = pd.DataFrame({"y": input_data.x})

        regressor.update_data(input_data, output_data)

        self.assertEqual(len(regressor.data_regression.split.full_input), 15)
        self.assertEqual(len(regressor.data_regression.split.full_output), 15)

        self.assertEqual(len(regressor.data_regression.scaled_split.full_input), 15)
        self.assertEqual(len(regressor.data_regression.scaled_split.full_output), 15)

    def test_random_state(self):
        "test the random state and verify that it is deterministic"
        parameters = generate_regression_parameters(count=100)
        parameters.random_state = 10

        regressor = GaussianRegressor(parameters)
        regressor.fit()

        regressor_2 = GaussianRegressor(parameters)
        regressor_2.fit()

        pd.testing.assert_series_equal(regressor.error_metrics(),
                                       regressor_2.error_metrics())

    def test_load_rebuild(self):
        "load the regressor with a different version of sklearn than it was saved with and auto-matically rebuild it"
        base_dir = Path(__file__).parent.parent.parent / "data"
        regressor_dir = base_dir / "regressor" / "gaussian"

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir = Path(temp_dir)

            #copy dir to temp_dir so that the original can't be modified
            shutil.copytree(regressor_dir, temp_dir, dirs_exist_ok=True)

            with self.assertLogs('gumps.solvers.regressors.regression_solver', level='WARNING') as cm:
                load_regressor(temp_dir, auto_resave=False)
            self.assertTrue('WARNING:gumps.solvers.regressors.regression_solver:Regressor failed to load, rebuilding regressor.' in cm.output)

    def test_load_rebuild_resave(self):
        "load the regressor with a different version of sklearn than it was saved with and auto-matically rebuild it"
        base_dir = Path(__file__).parent.parent.parent / "data"
        regressor_dir = base_dir / "regressor" / "gaussian"

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir = Path(temp_dir)

            #copy dir to temp_dir so that the original can't be modified
            shutil.copytree(regressor_dir, temp_dir, dirs_exist_ok=True)

            with self.assertLogs('gumps.solvers.regressors.regression_solver', level='WARNING') as cm:
                load_regressor(temp_dir, auto_resave=True, auto_rebuild=True)
            self.assertTrue('WARNING:gumps.solvers.regressors.regression_solver:Regressor failed to load, rebuilding regressor.' in cm.output)
            self.assertTrue('WARNING:gumps.solvers.regressors.regression_solver:Regressor was rebuilt, resaving regressor.' in cm.output)

    def test_load_exception(self):
        "load the regressor with a different version of sklearn and disallow auto-rebuild"
        base_dir = Path(__file__).parent.parent.parent / "data"
        regressor_dir = base_dir / "regressor" / "gaussian"

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir = Path(temp_dir)

            #copy dir to temp_dir so that the original can't be modified
            shutil.copytree(regressor_dir, temp_dir, dirs_exist_ok=True)

            with self.assertRaises(RuntimeError):
                load_regressor(temp_dir, auto_rebuild=False)

    def test_clone(self):
        "test the clone method"
        parameters = generate_regression_parameters()
        regressor = GaussianRegressor(parameters)
        new_regressor = regressor.clone(parameters)
        self.assertEqual(regressor.parameters, new_regressor.parameters)

    def test_clone_tune(self):
        "test the clone tune method"
        parameters = generate_regression_parameters()
        regressor = GaussianRegressor(parameters)
        with self.assertRaises(NotImplementedError):
            regressor.clone_tune(None)

    def test_auto_tune(self):
        "test the auto tune method"
        parameters = generate_regression_parameters()
        regressor = GaussianRegressor(parameters)
        with self.assertRaises(NotImplementedError):
            regressor.auto_tune(None)

    def test_get_tuned_parameters(self):
        "test the get tuned parameters method"
        parameters = generate_regression_parameters()
        regressor = GaussianRegressor(parameters)
        with self.assertRaises(NotImplementedError):
            regressor.get_tuned_parameters()

if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(TestGaussianRegressionSolver)
    unittest.TextTestRunner(verbosity=2).run(suite)