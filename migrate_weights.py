"""
将旧版 scikit-learn 保存的权重迁移到当前版本。
旧版 _gb_losses 模块已被移除，类名也有变化。
"""
import pickle
import joblib
import types
import sklearn.ensemble._gb as _gb

# 构造一个假的 _gb_losses 模块，把旧类名映射到新类名
_fake_losses = types.ModuleType("sklearn.ensemble._gb_losses")
_fake_losses.LeastSquaresError = _gb.HalfSquaredError
_fake_losses.LeastAbsoluteError = _gb.AbsoluteError
_fake_losses.HuberLossFunction = _gb.HuberLoss
_fake_losses.QuantileLossFunction = _gb.PinballLoss
_fake_losses.ExponentialLoss = _gb.ExponentialLoss
_fake_losses.MultinomialDeviance = _gb.HalfMultinomialLoss
_fake_losses.BinomialDeviance = _gb.HalfBinomialLoss

import sys
sys.modules["sklearn.ensemble._gb_losses"] = _fake_losses


class CompatUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        if module == "sklearn.ensemble._gb_losses":
            return getattr(_fake_losses, name)
        return super().find_class(module, name)


def migrate(src, dst):
    print(f"迁移: {src}")
    # joblib 内部用 pickle，注入兼容模块后直接 load 即可
    import sys
    sys.modules["sklearn.ensemble._gb_losses"] = _fake_losses
    model = joblib.load(src)
    joblib.dump(model, dst)
    print(f"  已保存: {dst}")
    return model


if __name__ == "__main__":
    weights_dir = "openage/models/weights"
    migrate(f"{weights_dir}/standard_21feat.joblib",  f"{weights_dir}/standard_21feat.joblib")
    migrate(f"{weights_dir}/extended_35feat.joblib", f"{weights_dir}/extended_35feat.joblib")
    print("\n完成，可以运行 test_age.py 了。")
