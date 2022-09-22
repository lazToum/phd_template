"""-*- coding: utf-8 -*-."""
import timeit


def main():
    # type: () -> None
    """Do stuff."""
    print("Hello World!")


if __name__ == "__main__":
    tic = timeit.default_timer()
    main()
    toc = timeit.default_timer()
    print(f"\nDone in {(toc - tic)} seconds\n")
