import time
import numpy as np
import matplotlib.pyplot as plt


def arrow():
    fig = plt.figure()
    ax = fig.add_subplot(111)

    point = {
        'start': [10, 10],
        'end': [90, 90],
        "v1": [20, 20],
        "v2": [30, 30],
        "v3": [40, 40],
    }

    ax.plot(*point['start'], 'o', color="red")
    ax.plot(*point['end'], 'o', color="blue")

    ax.annotate('', xy=point['end'], xytext=point['start'],
                arrowprops=dict(shrink=0, width=1, headwidth=8,
                                headlength=10, connectionstyle='arc3',
                                facecolor='gray', edgecolor='gray')
                )

    ax.set_xlim([0, 100])
    ax.set_ylim([0, 100])

    plt.show()
    # time.sleep(3)
    # plt.pause(1)
    fig.canvas.draw()
    fig.canvas.flush_events()
    ax.annotate('test', xy=point['v2'], xytext=point['v1'],
                arrowprops=dict(shrink=0, width=1, headwidth=8,
                                headlength=10, connectionstyle='arc3',
                                facecolor='gray', edgecolor='gray')
                )
    fig.canvas.draw()
    fig.canvas.flush_events()
    # plt.pause(1)
    an2: plt.Annotation = ax.annotate('test', xy=point['v3'], xytext=point['v1'],
                                      arrowprops=dict(shrink=0, width=1, headwidth=8,
                                      headlength=10, connectionstyle='arc3',
                                      facecolor='gray', edgecolor='gray')
                                      )
    fig.canvas.draw()
    fig.canvas.flush_events()
    an2.remove()
    # plt.show()
    fig.canvas.draw()
    fig.canvas.flush_events()


if __name__ == "__main__":
    arrow()
